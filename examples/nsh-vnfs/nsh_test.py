# we want  encode nsh-seq-nr and 1 bit information: in one bitstring:
a = 557
print(a)
b = 66
print(bin(a))
print("make space for b")
a = a << 32
print(bin(a))
print("integrate a in first pos")
print(bin(1) + "^" + bin(a))
a = a ^ b
print(bin(a))
print("fiddle out")
b_out = a & ((2 ** 32) - 1)
a_out = a >> 32
print("a is " + str(a_out))
print("b is " + str(b_out))
