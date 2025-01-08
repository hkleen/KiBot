import io
import yaml

with open('test.yaml') as f:
    txt = f.read()
data = yaml.safe_load(io.StringIO(txt))
print(data)
