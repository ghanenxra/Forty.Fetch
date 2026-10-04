import os
import ast

def get_ast_node_text(source, node):
    lines = source.splitlines()
    start = node.lineno - 1
    end = node.end_lineno
    return '\n'.join(lines[start:end])

def main():
    with open('main.py', 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    
    # Extract everything before FortyFetchApp
    app_cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FortyFetchApp')
    app_start_line = app_cls.lineno - 1
    
    preamble = '\n'.join(source.splitlines()[:app_start_line])
    
    # We will split preamble into config, utils, and widgets
    # For now, put all preamble into core/common.py
    os.makedirs('fortyfetch', exist_ok=True)
    os.makedirs('fortyfetch/core', exist_ok=True)
    os.makedirs('fortyfetch/ui', exist_ok=True)
    os.makedirs('fortyfetch/ui/views', exist_ok=True)
    
    with open('fortyfetch/core/common.py', 'w', encoding='utf-8') as f:
        f.write(preamble)
        
    # Group methods
    groups = {
        'settings': ['_load_settings', '_save_settings', '_update_setting'],
        'theme': ['set_theme', '_set_icon'],
        'layout': ['_build_layout', '_build_sidebar', 'switch_nav', '_build_header_bar', 'on_exit'],
        'home_view': ['_init_home_view', '_on_url_input_change', 'select_path', '_bring_popup_front'],
        'downloads_view': ['_init_downloads_view', '_render_download_card', '_clear_completed_downloads'],
        'settings_view': ['_init_settings_view'],
        'about_view': ['_init_about_view', 'show_update_help', 'show_donation_info'],
        'updater': [
            'check_bundled_tools', 'start_manual_update_thread', 'check_and_update_dependencies',
            '_fetch_latest_app_release_details', 'prompt_and_install_app_update',
            '_apply_manual_update_and_restart', '_check_and_update_tools', '_manual_update_ytdlp',
            '_manual_update_bundled_ffmpeg', '_fetch_latest_ytdlp_version', '_fetch_latest_ffmpeg_release',
            '_download_file', '_extract_ffmpeg_bins', '_get_ffmpeg_version', '_is_version_newer'
        ],
        'downloader': [
            '_resolve_ffmpeg_location', '_update_download_progress', 'progress_hook',
            'start_download_thread', '_format_for_quality', 'download_video', '_reset_after_download'
        ]
    }
    
    mixins = {}
    init_body = ""
    for m in app_cls.body:
        if isinstance(m, ast.FunctionDef):
            if m.name == '__init__':
                init_body = get_ast_node_text(source, m)
            else:
                found = False
                for group, methods in groups.items():
                    if m.name in methods:
                        if group not in mixins:
                            mixins[group] = []
                        mixins[group].append(get_ast_node_text(source, m))
                        found = True
                        break
                if not found:
                    print(f"UNMAPPED METHOD: {m.name}")
                    if 'misc' not in mixins: mixins['misc'] = []
                    mixins['misc'].append(get_ast_node_text(source, m))
                    
    # Write mixins
    mixin_files = {
        'settings': 'fortyfetch/core/settings.py',
        'updater': 'fortyfetch/core/updater.py',
        'downloader': 'fortyfetch/core/downloader.py',
        'theme': 'fortyfetch/ui/theme.py',
        'layout': 'fortyfetch/ui/layout.py',
        'home_view': 'fortyfetch/ui/views/home.py',
        'downloads_view': 'fortyfetch/ui/views/downloads.py',
        'settings_view': 'fortyfetch/ui/views/settings.py',
        'about_view': 'fortyfetch/ui/views/about.py',
        'misc': 'fortyfetch/core/misc.py'
    }
    
    imports_for_mixins = "from fortyfetch.core.common import *\nimport customtkinter as ctk\nimport threading\nimport os\nimport time\nimport json\nimport traceback\nimport subprocess\nimport re\nimport shutil\nimport webbrowser\nfrom tkinter import filedialog, messagebox\n\n"
    
    for group, code_blocks in mixins.items():
        if group not in mixin_files: continue
        class_name = ''.join(word.capitalize() for word in group.split('_')) + 'Mixin'
        with open(mixin_files[group], 'w', encoding='utf-8') as f:
            f.write(imports_for_mixins)
            f.write(f"class {class_name}:\n")
            for block in code_blocks:
                # Add indentation
                indented = '\n'.join('    ' + line if line else line for line in block.splitlines())
                f.write(indented + "\n\n")
                
    # Write new app.py
    mixin_classes = []
    app_imports = "import customtkinter as ctk\nimport sys\nimport os\n"
    app_imports += "from fortyfetch.core.common import *\n"
    for group in mixins.keys():
        mod = mixin_files[group].replace('/', '.').replace('\\', '.').replace('.py', '')
        class_name = ''.join(word.capitalize() for word in group.split('_')) + 'Mixin'
        app_imports += f"from {mod} import {class_name}\n"
        mixin_classes.append(class_name)
        
    bases = ", ".join(mixin_classes + ["ctk.CTk"])
    
    with open('fortyfetch/app.py', 'w', encoding='utf-8') as f:
        f.write(app_imports + "\n\n")
        f.write(f"class FortyFetchApp({bases}):\n")
        indented_init = '\n'.join('    ' + line if line else line for line in init_body.splitlines())
        f.write(indented_init + "\n")
        
    # Write new entry point
    with open('main_refactored.py', 'w', encoding='utf-8') as f:
        f.write("import sys\n")
        f.write("from fortyfetch.core.common import should_exit_early_for_packaged_relaunch\n")
        f.write("from fortyfetch.app import FortyFetchApp\n\n")
        f.write("def main():\n")
        f.write("    if should_exit_early_for_packaged_relaunch():\n")
        f.write("        sys.exit(0)\n")
        f.write("    app = FortyFetchApp()\n")
        f.write("    app.mainloop()\n\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    main()\n")

if __name__ == '__main__':
    main()
