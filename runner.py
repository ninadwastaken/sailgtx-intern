import argparse, subprocess, time, csv, os, shlex, tempfile, glob, shutil, sys
from pathlib import Path

SURYA_BIN  = "surya_ocr"
MARKER_BIN = "marker"

def run_cmd(label: str, cmd: str, cwd: str | None, timeout: int):
    print(f"[{label}] START: {cmd}"); sys.stdout.flush()
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        dt = time.time() - t0
        tail = (p.stderr or p.stdout or "")[-800:]
        print(f"[{label}] END rc={p.returncode} dt={dt:.2f}s")
        return dt, p.returncode, tail, False
    except subprocess.TimeoutExpired as e:
        dt = time.time() - t0
        tail = (getattr(e, "stderr", "") or getattr(e, "stdout", ""))[-800:]
        print(f"[{label}] TIMEOUT after {dt:.2f}s")
        return dt, 124, tail or "TIMEOUT", True

def dir_size_and_count(path: str) -> tuple[int,int]:
    total = files = 0
    for root,_,names in os.walk(path):
        for n in names:
            fp = os.path.join(root,n)
            try: total += os.path.getsize(fp); files += 1
            except OSError: pass
    return total, files

def run_surya(infile: str, outdir: str, timeout: int):
    stem = Path(infile).stem
    dest_dir = os.path.join(outdir, f"{stem}.surya")
    with tempfile.TemporaryDirectory() as td:
        local_in = os.path.join(td, Path(infile).name)
        tmp_out  = os.path.join(td, "surya_out")
        os.makedirs(tmp_out, exist_ok=True); shutil.copy2(infile, local_in)
        cmd = f"{SURYA_BIN} {shlex.quote(local_in)} --output_dir {shlex.quote(tmp_out)}"
        dt, rc, tail, to = run_cmd("SURYA", cmd, cwd=None, timeout=timeout)
        Path(outdir).mkdir(parents=True, exist_ok=True)
        if os.path.exists(dest_dir): shutil.rmtree(dest_dir)
        out_b=out_f=0
        if rc==0 and os.path.isdir(tmp_out):
            shutil.copytree(tmp_out, dest_dir)
            out_b, out_f = dir_size_and_count(dest_dir)
        return dt, rc, (tail + ("\n[timeout]" if to else "")), dest_dir, out_b, out_f

def run_marker(infile: str, outdir: str, timeout: int):
    stem = Path(infile).stem
    dest_md = os.path.join(outdir, f"{stem}.marker.md")
    with tempfile.TemporaryDirectory() as td:
        in_dir  = os.path.join(td, "in"); out_dir = os.path.join(td, "out")
        os.makedirs(in_dir, exist_ok=True); os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(infile, os.path.join(in_dir, Path(infile).name))
        # Put options BEFORE folder; also set sane defaults to avoid heavy pagination work
        cmd = f"{MARKER_BIN} {shlex.quote(in_dir)} --output_dir {shlex.quote(out_dir)}"
        dt, rc, tail, to = run_cmd("MARKER", cmd, cwd=None, timeout=timeout)
        Path(outdir).mkdir(parents=True, exist_ok=True)
        out_b=out_f=0
        if rc==0:
            md_files = sorted(glob.glob(os.path.join(out_dir, "**", "*.md"), recursive=True), key=os.path.getmtime)
            if md_files:
                shutil.copy2(md_files[0], dest_md)
                try: out_b = os.path.getsize(dest_md); out_f = 1
                except OSError: pass
        return dt, rc, (tail + ("\n[timeout]" if to else "")), dest_md, out_b, out_f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--tool", choices=["surya","marker","both"], default="both")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--logcsv", default="runs_log.csv")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    header = ["tool","input_pdf","output_path","runtime_s","return_code","output_bytes","output_files","stderr_tail"]
    new_file = not Path(args.logcsv).exists()
    rows=[]
    if args.tool in ("surya","both"):
        dt, rc, tail, outp, ob, of = run_surya(args.pdf, args.outdir, args.timeout)
        rows.append(["surya", args.pdf, outp, f"{dt:.3f}", rc, ob, of, tail])
    if args.tool in ("marker","both"):
        dt, rc, tail, outp, ob, of = run_marker(args.pdf, args.outdir, args.timeout)
        rows.append(["marker", args.pdf, outp, f"{dt:.3f}", rc, ob, of, tail])

    with open(args.logcsv, "a", newline="") as f:
        w=csv.writer(f)
        if new_file: w.writerow(header)
        w.writerows(rows)

    print("Logged runs:"); [print("  ", r) for r in rows]

if __name__ == "__main__":
    main()
# --- end ---
