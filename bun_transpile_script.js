const transpiler = Bun.Transpiler({ loader: "ts" });
const typescript = await Bun.file('./canvas.ts').text();
const javascript = await transpiler.transform(typescript);
Bun.write('canvas.js', javascript);
