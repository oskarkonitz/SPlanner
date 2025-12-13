from storage import load, save

def main():
    print("Planner - start")
    data = load()
    print("loaded data:")
    print(data)
    save(data)

if __name__ == '__main__':
    main()
