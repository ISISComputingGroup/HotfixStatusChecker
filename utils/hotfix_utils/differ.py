import os
import subprocess

paths_to_exclude = [r"tools/master/cygwin/"]
repo_dir = r"c:\instrument\apps\epics"
result = subprocess.run(
    ["cmd", "/c", f"cd /d {repo_dir} && git status --porcelain"],
    capture_output=True,
    text=True,
    check=False,
)
ext_to_check = [
    "db",
    "template",
    "substitutions",
    "cmd",
    "bat",
    "txt",
    "proto",
    "protocol",
    "req",
    "dmc",
    "gmc",
]
for line in result.stdout.strip().split("\n"):
    mode, file = line.split()
    file_lc = file.lower()
    exclude_path = False
    for path in paths_to_exclude:
        if file_lc.startswith(path):
            exclude_path = True
    if not exclude_path:
        exclude_ext = True
        for ext in ext_to_check:
            if file_lc.endswith("." + ext):
                exclude_ext = False
                remote_file = (
                    "//isis.cclrc.ac.uk/inst$/kits$/compgroup/"
                    f"icp/releases/26.2.0/EPICS/{file}"
                )
                if os.path.exists(remote_file):
                    result = subprocess.run(
                        [
                            "cmd",
                            "/c",
                            (
                                f"cd /d {repo_dir} && "
                                "git diff --no-index {file} {remote_file}"
                            ),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    print(result.stdout.strip())
                    print(result.stderr.strip())
                else:
                    print(f"{file} does not exist at remote")
        if exclude_ext:
            print(f"{file} was excluded from diff")
