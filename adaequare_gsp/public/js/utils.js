frappe.provide("modifyMethod");

modifyMethod = function (source, funcName, newFunc, before = false) {
  let sourceObj = eval(source);
  if (!sourceObj) {
    console.error(`Could not find object: ${source}`);
    return;
  }
  let isPrototype = false;
  let oldFunc = sourceObj[funcName];

  if (!oldFunc) {
    oldFunc = sourceObj.prototype[funcName];
    isPrototype = true;
  }

  if (!oldFunc) {
    console.error(`Function ${funcName} does not exist for ${source}`);
    return;
  }
  function newFunction() {
    if (before) {
      let msg = newFunc.apply(this, arguments);
      if (msg === "return") {
        return;
      }
    }

    let out = oldFunc.apply(this, arguments);
    let new_out;

    if (!before) {
      let execNewFunc = () => {
        return newFunc.call(this, ...Array.from(arguments), out);
      };
      if (typeof out === "object" && out.then) {
        return out.then(execNewFunc);
      } else {
        new_out = execNewFunc();
      }
    }

    return new_out || out;
  }
  if (isPrototype) {
    sourceObj.prototype[funcName] = newFunction;
  } else {
    sourceObj[funcName] = newFunction;
  }
};
