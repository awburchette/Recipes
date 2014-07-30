import hashlib

password = raw_input('Enter your password: ')
m = hashlib.sha512()
m.update(password)

with open('pass.txt', 'w') as f:
    f.write(m.hexdigest())
    
print 'You password hash is in pass.txt'