// Create new websocket connection
const socket = new WebSocket("ws://127.0.0.1:3002");
const mainCanvas = document.getElementById('main-canvas') as HTMLCanvasElement;
const ctx = mainCanvas.getContext("2d")!;
if (ctx == null) { console.error("Unable to get canvas context") }

const mouseData = {
    mouseX: 50,
    mouseY: 50,
    buttons: 0,
}

// socket.send(new ArrayBuffer(8))

socket.addEventListener("open", (event) => {
    console.log(event)
    alert("Websocket Connected")
})
socket.addEventListener("close", (event) => {
    console.log(event)
    alert("Websocket Disconnected")
})

const opcodes = {
    0x01: "fillRect",
    0x02: "strokeRect",
    0x03: "clearRect",

    0x10: "beginPath",
    0x11: "closePath",
    0x12: "stroke",
    0x13: "fill",

    0x20: "moveTo",
    0x21: "lineTo",
    0x22: "arc",
    0x23: "arcTo",

    0x30: "triangle",
    0x31: "triangleOutline",
    0x32: "circle",
    0x33: "circleOutline",

    0xFF: "changerColor"
}

function safetyChecks(raw: ArrayBuffer, expectedByteLength: number): number {
    if (raw.byteLength != expectedByteLength) { console.log("Malformed data"); return -1 };
    if (ctx == null) { console.log("canvas context null"); return -1 };
    return 1
}

const opHandlers = new Map<number, (raw: ArrayBuffer) => void>()
opHandlers.set(0x01, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 16) != 1) { return };
    let data = new Int32Array(raw);
    // console.log("Filling rectangle:", data)
    // ctx.fillStyle = "rgb(200 0 0)";
    ctx.fillRect(data[0], data[1], data[2], data[3]);
});
opHandlers.set(0x02, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 16) != 1) { return };
    let data = new Int32Array(raw);
    // console.log("Outlining rectangle:", data)
    // ctx.fillStyle = "rgb(200 0 0)";
    ctx.strokeRect(data[0], data[1], data[2], data[3]);
})
opHandlers.set(0x03, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 16) != 1) { return };
    let data = new Int32Array(raw);
    // console.log("Clearing:", data)
    // ctx.fillStyle = "rgb(200 0 0)";
    ctx.clearRect(data[0], data[1], data[2], data[3]);
})

opHandlers.set(0x10, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 0) != 1) { return };
    ctx.beginPath()
})
opHandlers.set(0x11, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 0) != 1) { return };
    ctx.closePath()
})
opHandlers.set(0x12, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 0) != 1) { return };
    ctx.stroke()
})
opHandlers.set(0x13, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 0) != 1) { return };
    ctx.fill()
})

opHandlers.set(0x30, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 24) != 1) { return };
    let data = new Int32Array(raw);
    ctx.beginPath();
    ctx.moveTo(data[0], data[1]);
    ctx.lineTo(data[2], data[3]);
    ctx.lineTo(data[4], data[5]);
    ctx.fill();
});
opHandlers.set(0x31, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 24) != 1) { return };
    let data = new Int32Array(raw);
    ctx.beginPath();
    ctx.moveTo(data[0], data[1]);
    ctx.lineTo(data[2], data[3]);
    ctx.lineTo(data[4], data[5]);
    ctx.stroke();
});

opHandlers.set(0x32, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 12) != 1) { return };
    let data = new Int32Array(raw);
    let x = data[0];
    let y = data[1];
    let r = data[2];
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2, true);
    ctx.fill();
});

opHandlers.set(0x33, (raw: ArrayBuffer) => {
    if (safetyChecks(raw, 12) != 1) { return };
    let data = new Int32Array(raw);
    let x = data[0];
    let y = data[1];
    let r = data[2];
    ctx.beginPath();
    ctx.arc(x-r/2, y-r/2, r, 0, Math.PI * 2, true);
    ctx.stroke();
});

opHandlers.set(0xFF, (raw: ArrayBuffer) => {
    let css_str = new TextDecoder().decode(raw);
    ctx.fillStyle = css_str;
});

function sendClientData() {
    let asInt = new Int32Array(6)
    asInt[1] = mainCanvas.width
    asInt[2] = mainCanvas.height
    asInt[3] = mouseData.mouseX
    asInt[4] = mouseData.mouseY
    asInt[5] = mouseData.buttons
    
    let asBytes = new Uint8Array(asInt.buffer)
    asBytes[0] = 0x00
    asBytes[1] = asInt.byteLength
    
    // console.log("Sending stuff")
    socket.send(asInt.buffer)
}

socket.addEventListener("message", async (event) => {
    // console.log('server: ' + event.data);
    // console.log("Frame recieved")
    // Send back mouse data and stuff first
    sendClientData()
    // Process the data from the server
    if (event.data instanceof String) { return }
    let raw = await event.data.arrayBuffer()
    if (raw.byteLength == 0) { return }

    let bytes = new Uint8Array(raw);
    let index = 0
    while (index < bytes.length) {
        let opcode = bytes[index];
        let len    = bytes[index + 1];
        let dataPart = raw.slice(index + 2, index + len)
        index += len;
        if (!opHandlers.has(opcode)) {
            console.error("Unknown Opcode:", opcode)
            continue
        } else {
            opHandlers.get(opcode)!(dataPart)
        }
    }

    // alert(event.data)
});

const draw = () => {
    if (ctx == null) { return };
    // ctx.fillStyle = "rgb(200 0 0)";
    // ctx.fillRect(10, 10, 50, 50);
    //
    // ctx.fillStyle = "rgb(0 0 200 / 50%)";
    // ctx.fillRect(30, 30, 50, 50);
};

window.addEventListener('resize', () => {
    mainCanvas.width = window.innerWidth;
    mainCanvas.height = window.innerHeight;
})

window.addEventListener('load', () => {
    // Resize the canvas to take up the whole page
    mainCanvas.width = window.innerWidth;
    mainCanvas.height = window.innerHeight;

    draw();
});

function mouseListener(event: MouseEvent) {
    mouseData.mouseX = event.clientX
    mouseData.mouseY = event.clientY
    mouseData.buttons = event.buttons
}

document.addEventListener('mousemove', mouseListener, false);
document.addEventListener('mousedown', mouseListener, false);
document.addEventListener('mouseup', mouseListener, false);
