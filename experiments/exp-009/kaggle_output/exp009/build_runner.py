import sys
sys.path.insert(0, '/kaggle/working/src')
if __name__ == '__main__':
    from invsqrt import generate
    generate.main(sys.argv[1:])
