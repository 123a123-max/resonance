// Resize before IndexedDB storage and transfer, rather than uploading camera originals.
export async function prepareImage(file: File, maxEdge = 1600, quality = .82): Promise<File> {
  if (file.size > 40 * 1024 * 1024) throw Error('图片超过 40MB，请选择较小的图片');
  const url = URL.createObjectURL(file);
  const img = new Image();
  try {
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = () => reject(Error('浏览器无法读取此图片格式，请在相册中导出为 JPEG 或 PNG 后选择'));
      img.src = url;
    });
    const scale = Math.min(1, maxEdge / Math.max(img.naturalWidth, img.naturalHeight));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
    const ctx = canvas.getContext('2d');
    if (!ctx) throw Error('无法处理图片，请稍后重试');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(b => b ? resolve(b) : reject(Error('图片转换失败')), 'image/jpeg', quality));
    canvas.width = canvas.height = 0;
    return new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', {type: 'image/jpeg'});
  } finally { URL.revokeObjectURL(url); }
}
