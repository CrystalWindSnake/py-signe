# py-signe

#### 介绍
按照 [S.js](https://github.com/adamhaile/S) 的核心机制，在 python 中实现的响应式系统

#### 安装
```shell
pip install signe
```

#### 使用
```python
from signe import createSignal, effect, computed

get_num, set_num = createSignal(1)

@computed
def plus1():
    return get_num() + 1


@effect
def _():
    print('plus1 is :',plus1())

# 此时控制台打印 `plus1 is :2`

set_num(10)

# 此时控制台打印 `plus1 is :11`


```

- `createSignal` 创建信号。信号包含2个主要函数，分别是 `getter` 与 `setter` 函数。
- `computed` 创建计算表达。其参数为一个函数。函数中使用信号的 `getter` 函数获取值，则此计算表达与信号自动产生关联。当信号的值变化时，计算表达也会自动触发改变。
- `effect` 本质上与 `computed` 一样。可以自动捕获信号或计算表达`computed`的改变，从而自动触发。



## 响应式设计流程

![alt text](image.png)

角色: 

- [signal](#signal): 可读写. 
- [computed](#computed): 只读，保存一个函数，并能获取计算值
- [effect](#effect)：保存一个函数，只负责执行
- [Scheduler](#scheduler)：全局调度执行。

---
### signal
signal 总是一个系统触发流程的源头

属性
1. value，保存值
2. caller list,记录下游调用自身的引用

方法
1. get value，返回 value 即可
2. set value，赋值，[流程](#signal赋值流程)



#### signal.赋值流程
任务，当值有更新时，应该通知[Scheduler](#scheduler)记录为一个变化点。并通知下游引用者，告知"你们引用的值来源有变化了"

1. 当值没有变化时，结束
2. 值变化时：
   - 调用 [Scheduler](#scheduler) 方法，收集自身
   - 递归下游所有节点，标记为 待更新 状态.[详细](#computed-标记更新状态)
   
---
### computed
computed 获取值时，根据情况，按需执行自身函数，并返回值。

> 与 effect 不一样，computed 只有在获取值时，才可能重新执行。

属性
1. value，保存值
2. caller list,记录下游调用自身的引用
3. fn，保存一个执行函数
4. state:整体. 'init' | 'need update' | 'stable'
    - init:已定义，但从未执行
    - need udpate:需要更新。表示如果有人获取值，需要执行 fn
    - stable
5. need update source,保存了更改自行需要更新状态的来源引用。当数组变化时，需要及时更新 state

方法
1. get value
    - 判断是否需要更新。只需要判断 更新状态来源列表是否为空即可。空表示不需要更新
        - 不需要更新，直接返回 value
        - 需要更新，执行 fn，计算值更新到 value，并返回。如果计算值与 value 不一致，代表自身为一个变化点，让系统记录，[详细](#computed-计算值后发现值有变化)

2. mark need update(signal or computed)，把入参放入 need update source 

3. remove need update(signal or computed)，把入参从 need update source 中移除

#### computed 计算值后发现值有变化
当 value 有更新时，需要告知系统及其下游引用者。

1. 调用 [Scheduler](#scheduler) 方法，收集自身
2. 遍历下游子节点，调用其 mark need update 方法。记录自身。[详细](#computed-标记更新状态)

#### computed 标记更新状态
当自身上游引用的一个 signal 值有变化时，此时应该标记自身为"待更新"状态。因为 computed 本质是让使用者计算函数并获取其结果。因此，当上游产生变化时，并不需要像 effect 一样，必需立刻执行函数。只有在被外部获取值时，才按需更新。并保证不能重复执行无效计算。


相关：
[为什么-computed-与-effect-不一样](#为什么-computed-与-effect-不一样)

---
### Effect
当上游有可能变化时，执行自身函数。

相关：
[为什么-computed-与-effect-不一样](#为什么-computed-与-effect-不一样)

---
### Scheduler
属性


方法
1. mark change points for signal(signal)，保存到signal变化列表
2. mark change points for computed(computed)computed 变化列表

---

### 为什么 computed 与 effect 不一样
computed 与 effect 看起来有许多相似的行为
- 保存了一个函数，并在某个时刻执行函数
- 上游节点有可能是 computed 或 signal 

但是，两者的主要职能是有明显差异，这决定了它们执行函数的时机差异

对于 computed 来说，只有当外部向其获取值时，computed 才需要根据情况决定是否执行函数。

对于 effect 来说，只要上游节点有更新或未知状态(可能需要更新)，它仍然需要执行。

考虑一种情况：
```python


a = Signal('old')

@computed
def cpx():
    return a.value + ' post'

@effect
def _():
    if a.value=='new':
        print(cpx.value)

a.value = 'new step 1' # point 1
a.value = 'new step 2' # point 2
```

执行到 `point 1` 之前，effect 被执行了。但是 computed 并没有执行。因为 computed 没有被调用 `.value` 获取值

执行到 `point 1` ，值产生变化
- a 被调度器标记为变化点。
- cpx 修改为 待更新 状态
- effect 修改为 待更新 状态





