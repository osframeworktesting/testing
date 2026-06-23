try:
    print("Input first number:  ")
    x=int(input())
    print("Input second number:  ")
    y=int(input())
    if y==0 :
        raise Exception("The denominator cant be 0")
    print(x/y)

except Exception as e:
    print(e)
    print("In exception block")
else:
    print("In else block")
finally:
    print("This is always executed")