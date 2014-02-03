import sys
sys.path.insert(0, "src")
import multitail2

mt = multitail2.MultiTail(sys.argv[1], skip_to_end = False)

last = None
index = 0

while True:
   last_index = index
   for record in mt.poll():
      last = record
      index += 1
   if index == last_index:
      break
   print index

print repr(last)
   
