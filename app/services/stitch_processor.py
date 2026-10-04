import subprocess
import uuid
from pathlib import Path

import imageio_ffmpeg

from app.config import settings


class StitchProcessor:
    """Concatenates approved video clips into one output using FFmpeg's concat demuxer."""

    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        self.uploads_dir = Path(settings.MEDIA_UPLOADS_DIR).resolve()
        self.stitched_dir = Path(settings.MEDIA_STITCHED_DIR).resolve()
        self.stitched_dir.mkdir(parents=True, exist_ok=True)


    def stitch(self, project_id: str, ordered_filenames: list[str]) -> str:
        """
        Concatenate the given clip filenames (in order) into one MP4.
        Returns the public URL of the stitched output.
        """
        if not ordered_filenames:
            raise ValueError("No clips to stitch")

        # Validate all files exist
        paths: list[Path] = []
        for name in ordered_filenames:
            p = self.uploads_dir / name
            if not p.exists():
                raise FileNotFoundError(f"Missing clip: {name}")
            paths.append(p)

        # Create concat list file (FFmpeg concat demuxer format)
        list_file = self.stitched_dir / f"{project_id}_concat.txt"
        with list_file.open("w", encoding="utf-8") as f:
            for p in paths:
                # FFmpeg requires forward slashes and single quotes escaped
                safe = str(p).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{safe}'\n")

        # Output filename
        out_name = f"{project_id}_{uuid.uuid4().hex[:8]}.mp4"
        out_path = self.stitched_dir / out_name

        # Run FFmpeg concat (stream copy — fast, lossless)
        cmd = [
            self.ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Cleanup the temp list file
        try:
            list_file.unlink()
        except OSError:
            pass

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

        return f"/media/stitched/{out_name}"
