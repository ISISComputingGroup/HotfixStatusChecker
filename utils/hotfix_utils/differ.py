import os
import subprocess
import sys

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
    "py",
    "xml",
    "sql",
    "ini",
    "/",  # to check directories
]

ext_to_exclude = [
    "lib",
    "dll",
    "exe",
    "dbd",
    "opi",
    "bob",
    "adl",
    "ui",
    "obj",
    "so",
    "a",
    "c",
    "h",
]

if len(sys.argv) > 1 and sys.argv[1] == "x":
    use_exclude_list = True
else:
    use_exclude_list = False

for line in result.stdout.strip().split("\n"):
    mode, file = line.split()[0:2]
    file_lc = file.lower()
    exclude_path = False
    for path in paths_to_exclude:
        if file_lc.startswith(path):
            exclude_path = True
    if not exclude_path:
        if use_exclude_list:
            exclude_ext = False
            for ext in ext_to_exclude:
                if file_lc.endswith("." + ext):
                    exclude_ext = True
        else:
            exclude_ext = True
            for ext in ext_to_check:
                if (file_lc.endswith("." + ext)) or (ext == "/" and file.endswith(ext)):
                    exclude_ext = False
        if not exclude_ext:
            remote_file = (
                "//isis.cclrc.ac.uk/inst$/kits$/CompGroup/"
                f"ICP/EPICS/EPICS_CLEAN_win_x64/BUILD-2366/EPICS/{file}"
            )
            if os.path.exists(remote_file):
                result = subprocess.run(
                    [
                        "cmd",
                        "/c",
                        (
                            f"cd /d {repo_dir} && "
                            f"git diff -w --no-index {file} {remote_file}"
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
        else:
            print(f"{file} was excluded from diff")
