from datetime import datetime, date, timezone, timedelta
from io import BytesIO
import os, hashlib
from pathlib import Path
import secrets, shutil, json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from pydantic import BaseModel
from sqlalchemy import create_engine, String, Integer, DateTime, Date, Text, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

register_heif_opener(thumbnails=False)

# Diary dates use Beijing time even when the hosting server uses UTC.
DIARY_TIMEZONE = timezone(timedelta(hours=8))
def diary_day(now: datetime | None = None) -> date:
    return (now or datetime.now(timezone.utc)).astimezone(DIARY_TIMEZONE).date()

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def utc_timestamp(value: datetime) -> str:
    # Historical SQLite rows are naive UTC; do not reinterpret them as server local time.
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

ROOT = Path(os.environ.get('PLOG_DATA_DIR', str(Path(__file__).resolve().parent)))
ROOT.mkdir(parents=True, exist_ok=True)
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{ROOT / 'plog.db'}", connect_args={"check_same_thread": False, "timeout": 5}, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass
class Group(Base):
    __tablename__ = 'groups'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    invite_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    collection_time: Mapped[str] = mapped_column(String(5), default='00:00')
    owner_member_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
class Member(Base):
    __tablename__ = 'members'
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    nickname: Mapped[str] = mapped_column(String(80))
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    recovery_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
class Archive(Base):
    __tablename__ = 'archives'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    date: Mapped[str] = mapped_column(String(20))
    payload: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Moment(Base):
    __tablename__ = 'moments'
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id'))
    kind: Mapped[str] = mapped_column(String(10))
    media_url: Mapped[str] = mapped_column(String(300))
    caption: Mapped[str] = mapped_column(Text, default='')
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day: Mapped[date] = mapped_column(Date, default=diary_day)
    withdrawn: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

Base.metadata.create_all(engine)
try:
    with engine.begin() as conn:
        cols=[row[1] for row in conn.execute(text('PRAGMA table_info(members)'))]
        if 'avatar' not in cols: conn.execute(text('ALTER TABLE members ADD COLUMN avatar TEXT'))
        if 'recovery_hash' not in cols: conn.execute(text('ALTER TABLE members ADD COLUMN recovery_hash VARCHAR(64)'))
except Exception:
    pass
with engine.begin() as conn:
    try: conn.execute(text('ALTER TABLE groups ADD COLUMN owner_member_id INTEGER'))
    except Exception: pass
    try: conn.execute(text('UPDATE groups SET owner_member_id=(SELECT MIN(id) FROM members WHERE members.group_id=groups.id) WHERE owner_member_id IS NULL'))
    except Exception: pass
app = FastAPI(title='一页共同日记 API')
@app.middleware('http')
async def fresh_application(request, call_next):
    response = await call_next(request)
    if request.url.path in ('/', '/index.html', '/sw.js') or request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
app.mount('/uploads', StaticFiles(directory=UPLOADS), name='uploads')

class GroupCreate(BaseModel): name: str; nickname: str | None = None
class MemberCreate(BaseModel):
    nickname: str
    recovery_code: str | None = None
class MemberUpdate(BaseModel): nickname: str | None = None; avatar: str | None = None
class SettingsUpdate(BaseModel): collection_time: str

@app.get('/api/groups/{group_id}/archives')
def list_archives(group_id: int, include_deleted: bool=False):
    db=SessionLocal(); q=db.query(Archive).filter_by(group_id=group_id)
    if not include_deleted: q=q.filter(Archive.deleted_at.is_(None))
    return [{'id':a.id,'date':a.date,'payload':json.loads(a.payload),'deleted_at':utc_timestamp(a.deleted_at) if a.deleted_at else None} for a in q.order_by(Archive.created_at.desc()).all()]

@app.post('/api/groups/{group_id}/archives')
def save_archive(group_id: int, payload: dict):
    db=SessionLocal(); g=db.get(Group,group_id)
    if not g: raise HTTPException(404,'小组不存在')
    a=db.get(Archive,payload.get('id')) or Archive(id=payload.get('id'),group_id=group_id,date=payload.get('date',''),payload=json.dumps(payload,ensure_ascii=False))
    a.group_id=group_id; a.date=payload.get('date',''); a.payload=json.dumps(payload,ensure_ascii=False); a.deleted_at=None; db.add(a); db.commit(); return {'ok':True,'id':a.id}

@app.delete('/api/archives/{archive_id}')
def delete_archive(archive_id: str, requester_id: int):
    db=SessionLocal(); a=db.get(Archive,archive_id); g=db.get(Group,a.group_id) if a else None
    if not a: raise HTTPException(404,'归档不存在')
    if not g or requester_id!=g.owner_member_id: raise HTTPException(403,'只有创建者可以删除归档')
    a.deleted_at=utc_now(); db.commit(); return {'ok':True}

@app.patch('/api/archives/{archive_id}/restore')
def restore_archive(archive_id: str, requester_id: int):
    db=SessionLocal(); a=db.get(Archive,archive_id); g=db.get(Group,a.group_id) if a else None
    if not a: raise HTTPException(404,'归档不存在')
    if not g or requester_id!=g.owner_member_id: raise HTTPException(403,'只有创建者可以恢复归档')
    a.deleted_at=None; db.commit(); return {'ok':True}

@app.delete('/api/groups/{group_id}/archives/trash')
def empty_archive_trash(group_id: int, requester_id: int):
    db=SessionLocal(); g=db.get(Group,group_id)
    if not g or requester_id!=g.owner_member_id: raise HTTPException(403,'只有创建者可以清空回收站')
    db.query(Archive).filter_by(group_id=group_id).filter(Archive.deleted_at.is_not(None)).delete(synchronize_session=False); db.commit(); return {'ok':True}

@app.get('/api/health')
def health(): return {'ok': True}
@app.post('/api/groups')
def create_group(payload: GroupCreate):
    db=SessionLocal(); g=Group(name=payload.name, invite_code=secrets.token_urlsafe(6)[:8].upper()); db.add(g); db.commit(); db.refresh(g)
    m=Member(group_id=g.id,nickname=(payload.nickname or '你').strip()[:30] or '你'); db.add(m); db.commit(); g.owner_member_id=m.id; db.commit(); return {'id':g.id,'name':g.name,'invite_code':g.invite_code,'collection_time':g.collection_time,'owner_member_id':m.id}
@app.get('/api/groups/by-invite/{code}')
def find_group(code: str):
    db=SessionLocal(); g=db.query(Group).filter_by(invite_code=code.upper()).first()
    if not g: raise HTTPException(404,'小组不存在')
    return {'id':g.id,'name':g.name,'invite_code':g.invite_code,'collection_time':g.collection_time,'owner_member_id':g.owner_member_id}
@app.post('/api/groups/{group_id}/invite')
def create_invite(group_id: int):
    db=SessionLocal(); g=db.get(Group, group_id)
    if not g: raise HTTPException(404,'小组不存在')
    return {'group_id':g.id,'invite_code':g.invite_code}

@app.get('/api/groups/{group_id}/settings')
def get_settings(group_id: int):
    db=SessionLocal(); g=db.get(Group, group_id)
    if not g: raise HTTPException(404,'小组不存在')
    return {'collection_time':g.collection_time}

@app.post('/api/groups/{group_id}/members')
def add_member(group_id: int, payload: MemberCreate):
    db=SessionLocal();
    if not db.get(Group,group_id): raise HTTPException(404,'小组不存在')
    if payload.recovery_code:
        digest=hashlib.sha256(payload.recovery_code.strip().upper().encode()).hexdigest()
        m=db.query(Member).filter_by(group_id=group_id,recovery_hash=digest).first()
        if not m: raise HTTPException(403,'识别码不正确或成员已被移除，请勿重复创建成员')
        return {'id':m.id,'nickname':m.nickname,'avatar':m.avatar,'recovery_code':payload.recovery_code.strip().upper()}
    code=secrets.token_hex(12).upper()
    m=Member(group_id=group_id,nickname=payload.nickname,recovery_hash=hashlib.sha256(code.encode()).hexdigest()); db.add(m); db.commit(); db.refresh(m)
    return {'id':m.id,'nickname':m.nickname,'avatar':m.avatar,'recovery_code':code}
@app.delete('/api/members/{member_id}')
def remove_member(member_id: int, requester_id: int):
    db=SessionLocal(); m=db.get(Member, member_id)
    if not m: raise HTTPException(404,'成员不存在')
    g=db.get(Group, m.group_id)
    if not g or g.owner_member_id != requester_id: raise HTTPException(403,'只有创建者可以移出成员')
    if member_id == g.owner_member_id: raise HTTPException(400,'创建者不能移出自己')
    db.delete(m); db.commit(); return {'ok':True,'member_id':member_id}

@app.patch('/api/members/{member_id}')
def update_member(member_id: int, payload: MemberUpdate):
    db=SessionLocal(); m=db.get(Member, member_id)
    if not m: raise HTTPException(404,'成员不存在')
    if payload.nickname is not None:
        name=payload.nickname.strip()[:30]
        if not name: raise HTTPException(400,'昵称不能为空')
        m.nickname=name
    if payload.avatar is not None: m.avatar=payload.avatar
    db.commit(); return {'id':m.id,'nickname':m.nickname,'avatar':m.avatar}
@app.get('/api/groups/{group_id}')
def group_detail(group_id: int):
    db=SessionLocal(); g=db.get(Group,group_id)
    if not g: raise HTTPException(404,'小组不存在')
    members=db.query(Member).filter_by(group_id=group_id).all(); return {'id':g.id,'name':g.name,'invite_code':g.invite_code,'collection_time':g.collection_time,'owner_member_id':g.owner_member_id,'members':[{'id':m.id,'nickname':m.nickname,'avatar':m.avatar} for m in members]}
@app.patch('/api/groups/{group_id}/settings')
def update_settings(group_id: int, payload: SettingsUpdate):
    if len(payload.collection_time)!=5 or payload.collection_time[2]!=':': raise HTTPException(400,'时间格式应为 HH:MM')
    db=SessionLocal(); g=db.get(Group,group_id)
    if not g: raise HTTPException(404,'小组不存在')
    g.collection_time=payload.collection_time; db.commit(); return {'collection_time':g.collection_time}
@app.post('/api/groups/{group_id}/moments')
def upload_moment(group_id: int, member_id: int=Form(...), caption: str=Form(''), file: UploadFile=File(...), duration: int|None=Form(None)):
    db=SessionLocal();
    group=db.get(Group,group_id); member=db.get(Member,member_id)
    if not group or not member or member.group_id != group_id: raise HTTPException(404,'小组或成员不存在')
    is_video=(file.content_type or '').startswith('video/')
    if is_video and (duration is None or duration < 8 or duration > 60): raise HTTPException(400,'视频时长必须为 8～60 秒')
    ext = Path(file.filename or '').suffix.lower() or ('.mp4' if is_video else '.jpg')
    image_data = None
    if not is_video and (ext in {'.heic', '.heif'} or file.content_type in {'image/heic', 'image/heif'}):
        if file.size is not None and file.size > 40 * 1024 * 1024:
            raise HTTPException(413, '图片超过 40MB，请选择较小的图片')
        try:
            with Image.open(file.file) as image:
                if image.format != 'HEIF':
                    raise UnidentifiedImageError('Expected a HEIF image')
                image = ImageOps.exif_transpose(image)
                image.thumbnail((1600, 1600))
                with BytesIO() as buffer:
                    image.convert('RGB').save(buffer, format='JPEG', quality=82)
                    image_data = buffer.getvalue()
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            raise HTTPException(422, '无法读取这张 HEIC 照片，请尝试用相册导出为 JPEG') from error
        ext = '.jpg'
    name = f'{secrets.token_hex(12)}{ext}'
    target = UPLOADS / name
    if image_data is not None:
        target.write_bytes(image_data)
    else:
        with target.open('wb') as out:
            shutil.copyfileobj(file.file, out)
    m=Moment(group_id=group_id,member_id=member_id,kind='video' if is_video else 'image',media_url=f'/uploads/{name}',caption=caption,duration=duration,day=diary_day()); db.add(m); db.commit(); db.refresh(m)
    return {'id':m.id,'kind':m.kind,'media_url':m.media_url,'caption':m.caption,'duration':m.duration,'day':str(m.day),'created_at':utc_timestamp(m.created_at)}
@app.get('/api/groups/{group_id}/moments')
def list_moments(group_id: int, day: date|None=None):
    db=SessionLocal(); q=db.query(Moment).filter_by(group_id=group_id,withdrawn=0); items=q.filter_by(day=day or diary_day()).order_by(Moment.created_at).all(); return [{'id':m.id,'member_id':m.member_id,'kind':m.kind,'media_url':m.media_url,'caption':m.caption,'duration':m.duration,'created_at':utc_timestamp(m.created_at)} for m in items]
@app.patch('/api/groups/{group_id}/moments/clear')
def clear_group_moments(group_id: int, requester_id: int, day: date|None=None):
    db=SessionLocal(); g=db.get(Group, group_id)
    if not g: raise HTTPException(404,'小组不存在')
    q=db.query(Moment).filter_by(group_id=group_id, withdrawn=0)
    if day is not None:
        q=q.filter_by(day=day)
    if requester_id != g.owner_member_id:
        q=q.filter_by(member_id=requester_id)
    count=q.update({Moment.withdrawn:1}, synchronize_session=False); db.commit()
    return {'ok':True,'count':count}
@app.patch('/api/moments/{moment_id}/withdraw')
def withdraw(moment_id: int, requester_id: int):
    db=SessionLocal(); m=db.get(Moment,moment_id)
    if not m: raise HTTPException(404,'记录不存在')
    g=db.get(Group,m.group_id)
    if not g or (requester_id != g.owner_member_id and requester_id != m.member_id): raise HTTPException(403,'只能撤回自己的记录，创建者可以撤回全部记录')
    m.withdrawn=1; db.commit(); return {'ok':True}

# Register after API routes so the built frontend shares the API origin.
FRONTEND = Path(__file__).resolve().parent.parent / 'dist'
if FRONTEND.is_dir():
    app.mount('/', StaticFiles(directory=FRONTEND, html=True), name='resonance-web')
