let safetyChecks = function(raw, expectedByteLength) {
  if (raw.byteLength != expectedByteLength) {
    console.log("Malformed data");
    return -1;
  }
  if (ctx == null) {
    console.log("canvas context null");
    return -1;
  }
  return 1;
}, sendClientData = function() {
  let asInt = new Int32Array(6);
  asInt[1] = mainCanvas.width;
  asInt[2] = mainCanvas.height;
  asInt[3] = mouseData.mouseX;
  asInt[4] = mouseData.mouseY;
  asInt[5] = mouseData.buttons;
  let asBytes = new Uint8Array(asInt.buffer);
  asBytes[0] = 0;
  asBytes[1] = asInt.byteLength;
  socket.send(asInt.buffer);
}, mouseListener = function(event) {
  mouseData.mouseX = event.clientX;
  mouseData.mouseY = event.clientY;
  mouseData.buttons = event.buttons;
};
const socket = new WebSocket("ws://127.0.0.1:3002");
const mainCanvas = document.getElementById("main-canvas");
const ctx = mainCanvas.getContext("2d");
if (ctx == null) {
  console.error("Unable to get canvas context");
}
const mouseData = {
  mouseX: 50,
  mouseY: 50,
  buttons: 0
};
socket.addEventListener("open", (event) => {
  console.log(event);
  alert("Websocket Connected");
});
socket.addEventListener("close", (event) => {
  console.log(event);
  alert("Websocket Disconnected");
});
const opcodes = {
  1: "fillRect",
  2: "strokeRect",
  3: "clearRect",
  16: "beginPath",
  17: "closePath",
  18: "stroke",
  19: "fill",
  32: "moveTo",
  33: "lineTo",
  34: "arc",
  35: "arcTo",
  48: "triangle",
  49: "triangleOutline",
  50: "circle",
  51: "circleOutline",
  255: "changerColor"
};
const opHandlers = new Map;
opHandlers.set(1, (raw) => {
  if (safetyChecks(raw, 16) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  ctx.fillRect(data[0], data[1], data[2], data[3]);
});
opHandlers.set(2, (raw) => {
  if (safetyChecks(raw, 16) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  ctx.strokeRect(data[0], data[1], data[2], data[3]);
});
opHandlers.set(3, (raw) => {
  if (safetyChecks(raw, 16) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  ctx.clearRect(data[0], data[1], data[2], data[3]);
});
opHandlers.set(16, (raw) => {
  if (safetyChecks(raw, 0) != 1) {
    return;
  }
  ctx.beginPath();
});
opHandlers.set(17, (raw) => {
  if (safetyChecks(raw, 0) != 1) {
    return;
  }
  ctx.closePath();
});
opHandlers.set(18, (raw) => {
  if (safetyChecks(raw, 0) != 1) {
    return;
  }
  ctx.stroke();
});
opHandlers.set(19, (raw) => {
  if (safetyChecks(raw, 0) != 1) {
    return;
  }
  ctx.fill();
});
opHandlers.set(48, (raw) => {
  if (safetyChecks(raw, 24) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  ctx.beginPath();
  ctx.moveTo(data[0], data[1]);
  ctx.lineTo(data[2], data[3]);
  ctx.lineTo(data[4], data[5]);
  ctx.fill();
});
opHandlers.set(49, (raw) => {
  if (safetyChecks(raw, 24) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  ctx.beginPath();
  ctx.moveTo(data[0], data[1]);
  ctx.lineTo(data[2], data[3]);
  ctx.lineTo(data[4], data[5]);
  ctx.stroke();
});
opHandlers.set(50, (raw) => {
  if (safetyChecks(raw, 12) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  let x = data[0];
  let y = data[1];
  let r = data[2];
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2, true);
  ctx.fill();
});
opHandlers.set(51, (raw) => {
  if (safetyChecks(raw, 12) != 1) {
    return;
  }
  let data = new Int32Array(raw);
  let x = data[0];
  let y = data[1];
  let r = data[2];
  ctx.beginPath();
  ctx.arc(x - r / 2, y - r / 2, r, 0, Math.PI * 2, true);
  ctx.stroke();
});
opHandlers.set(255, (raw) => {
  let css_str = new TextDecoder().decode(raw);
  ctx.fillStyle = css_str;
});
socket.addEventListener("message", async (event) => {
  sendClientData();
  if (event.data instanceof String) {
    return;
  }
  let raw = await event.data.arrayBuffer();
  if (raw.byteLength == 0) {
    return;
  }
  let bytes = new Uint8Array(raw);
  let index = 0;
  while (index < bytes.length) {
    let opcode = bytes[index];
    let len = bytes[index + 1];
    let dataPart = raw.slice(index + 2, index + len);
    index += len;
    if (!opHandlers.has(opcode)) {
      console.error("Unknown Opcode:", opcode);
      continue;
    } else {
      opHandlers.get(opcode)(dataPart);
    }
  }
});
const draw = () => {
  if (ctx == null) {
    return;
  }
};
window.addEventListener("resize", () => {
  mainCanvas.width = window.innerWidth;
  mainCanvas.height = window.innerHeight;
});
window.addEventListener("load", () => {
  mainCanvas.width = window.innerWidth;
  mainCanvas.height = window.innerHeight;
  draw();
});
document.addEventListener("mousemove", mouseListener, false);
document.addEventListener("mousedown", mouseListener, false);
document.addEventListener("mouseup", mouseListener, false);
