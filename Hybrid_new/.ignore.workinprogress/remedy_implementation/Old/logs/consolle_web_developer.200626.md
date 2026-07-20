alpine.js:1 Alpine Expression Error: runCycle is not defined

Expression: "runCycle()"

 <button class=​"btn btn-run" @click=​"runCycle()​" :disabled=​"loading" style=​"width:​ 100%;​">​…​</button>​
te @ alpine.js:1
(anonymous) @ alpine.js:5
Promise.catch
(anonymous) @ alpine.js:5
nr @ alpine.js:1
(anonymous) @ alpine.js:5
o @ alpine.js:5
(anonymous) @ alpine.js:5
a @ alpine.js:5
alpine.js:5 Uncaught ReferenceError: runCycle is not defined
    at [Alpine] runCycle() (eval at <anonymous> (alpine.js:5:665), <anonymous>:3:16)
    at alpine.js:5:1068
    at nr (alpine.js:1:5082)
    at alpine.js:5:38898
    at o (alpine.js:5:27707)
    at alpine.js:5:28706
    at HTMLButtonElement.a (alpine.js:5:27729)