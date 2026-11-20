"""Copy the rendered entry to the required output location."""

from pathlib import Path
import shutil


def main():
    source = Path(__file__).resolve().parent / 'frontpage.png'
    destination = Path('/output/entry.png')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


if __name__ == '__main__':
    main()
