import sys
from fortyfetch.core.common import should_exit_early_for_packaged_relaunch
from fortyfetch.app import FortyFetchApp

def main():
    if should_exit_early_for_packaged_relaunch():
        sys.exit(0)
    app = FortyFetchApp()
    app.mainloop()

if __name__ == '__main__':
    main()
