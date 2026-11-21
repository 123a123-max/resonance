// SQLite's existing timestamps are naive UTC. Keep supporting older API versions.
export function parseServerTime(value: string): number {
  const normalized = value.trim().replace(' ', 'T');
  return Date.parse(/[zZ]$|[+-]\d{2}:?\d{2}$/.test(normalized) ? normalized : normalized + 'Z');
}

// Diary days follow Beijing time, including when the server runs in UTC.
export function diaryDate(value: number = Date.now()): string {
  return new Date(value + 8 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

export function uploadTime(value: number): string {
  return Number.isFinite(value) ? new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(value) : '时间未知';
}
