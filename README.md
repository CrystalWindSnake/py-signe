# py-signe

[中文文档](./README.cn.md)


#### Introduction
A responsive system implemented in python with reference to the core mechanisms of [S.js](https://github.com/adamhaile/S) and [vue reactivity](https://github.com/vuejs/core/tree/main/packages/reactivity). 


#### Installation
```shell
pip install signe
```



#### 使用
```python
from signe import signal, effect, computed

num = signal(1)

@computed
def plus1():
    return num.value + 1


@effect
def _():
    print('plus1 is :',plus1.value)

# should print `plus1 is :2`

num.value=10

# should print `plus1 is :11`


```

- `signal` Creates a signal. Reads and writes via `.value`.
- `computed` Creates a computed expression. The argument is a function. When a signal (`signal.value`) is used in the function to get a value, this calculation expression is automatically associated with the signal. When the value of the signal changes, the computed expression is automatically triggered to change.
- `effect` is essentially the same as `computed`. A change in the signal or `computed` expression is automatically captured and triggered.