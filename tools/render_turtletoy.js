#!/usr/bin/env node
// Execute a Turtletoy sketch locally and capture its turtle strokes as SVG.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

function usage() {
    console.error("usage: node tools/render_turtletoy.js INPUT.js OUTPUT.svg");
    process.exit(2);
}

if (process.argv.length !== 4) usage();

const input = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const source = fs.readFileSync(input, "utf8");
const strokes = [];
const turtles = [];
let penOpacity = 1;

class Turtle {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.angle = 90;
        this.penDown = true;
        this.current = null;
        turtles.push(this);
    }

    _flush() {
        if (this.current && this.current.length > 1) strokes.push(this.current);
        this.current = null;
    }

    penup() { this._flush(); this.penDown = false; return this; }
    pendown() { this.penDown = true; return this; }
    pu() { return this.penup(); }
    pd() { return this.pendown(); }
    up() { return this.penup(); }
    down() { return this.pendown(); }

    jump(x, y) {
        this._flush();
        if (Array.isArray(x)) [x, y] = x;
        this.x = Number(x);
        this.y = Number(y);
        return this;
    }

    goto(x, y) {
        if (Array.isArray(x)) [x, y] = x;
        if (this.penDown) {
            if (!this.current) this.current = [[this.x, this.y]];
            this.current.push([Number(x), Number(y)]);
        }
        this.x = Number(x);
        this.y = Number(y);
        return this;
    }

    setpos(x, y) { return this.goto(x, y); }
    setposition(x, y) { return this.goto(x, y); }
    setx(x) { return this.goto(x, this.y); }
    sety(y) { return this.goto(this.x, y); }
    forward(distance) {
        const angle = this.angle * Math.PI / 180;
        return this.goto(
            this.x + Math.cos(angle) * distance,
            this.y + Math.sin(angle) * distance
        );
    }
    fd(distance) { return this.forward(distance); }
    backward(distance) { return this.forward(-distance); }
    bk(distance) { return this.forward(-distance); }
    back(distance) { return this.forward(-distance); }
    right(angle) { this.angle -= angle; return this; }
    rt(angle) { return this.right(angle); }
    left(angle) { this.angle += angle; return this; }
    lt(angle) { return this.left(angle); }
    setheading(angle) { this.angle = angle; return this; }
    seth(angle) { return this.setheading(angle); }
    home() { this.jump(0, 0); this.angle = 90; return this; }
    position() { return [this.x, this.y]; }
    pos() { return this.position(); }
    xcor() { return this.x; }
    x() { return this.x; }
    ycor() { return this.y; }
    y() { return this.y; }
    heading() { return this.angle; }
    h() { return this.angle; }
    isdown() { return this.penDown; }
    clone() {
        const copy = new Turtle();
        copy.x = this.x;
        copy.y = this.y;
        copy.angle = this.angle;
        copy.penDown = this.penDown;
        return copy;
    }
    distance(x, y) {
        if (Array.isArray(x)) [x, y] = x;
        return Math.hypot(Number(x) - this.x, Number(y) - this.y);
    }
    towards(x, y) {
        if (Array.isArray(x)) [x, y] = x;
        return Math.atan2(Number(y) - this.y, Number(x) - this.x) * 180 / Math.PI - this.angle;
    }
    circle(radius, extent = 360, steps = undefined) {
        const count = steps || Math.max(12, Math.ceil(Math.abs(extent) / 3));
        const cx = this.x + Math.cos(this.angle * Math.PI / 180) * radius;
        const cy = this.y + Math.sin(this.angle * Math.PI / 180) * radius;
        const start = Math.atan2(this.y - cy, this.x - cx);
        const direction = radius >= 0 ? 1 : -1;
        for (let i = 1; i <= count; i++) {
            const angle = start + direction * (extent * Math.PI / 180) * i / count;
            this.goto(cx + Math.cos(angle) * Math.abs(radius), cy + Math.sin(angle) * Math.abs(radius));
        }
        this.angle += direction * extent;
        return this;
    }
}

const Canvas = {
    setpenopacity(value) { penOpacity = Number(value); },
};

const context = vm.createContext({ Canvas, Turtle });
vm.runInContext(source, context, { filename: input });
if (typeof context.walk !== "function") {
    throw new Error("Turtletoy sketch does not define walk(i)");
}

let index = 0;
while (context.walk(index)) {
    index += 1;
    if (index > 100000) throw new Error("walk() exceeded 100000 calls");
}

// Capture any strokes still held by turtles created in the sketch.
for (const turtle of turtles) turtle._flush();

const points = strokes.flat();
if (!points.length) throw new Error("Turtletoy sketch produced no strokes");
const minX = Math.min(...points.map(([x]) => x));
const maxX = Math.max(...points.map(([x]) => x));
const minY = Math.min(...points.map(([, y]) => y));
const maxY = Math.max(...points.map(([, y]) => y));
const margin = 5;
const viewMinX = Math.floor(minX - margin);
const viewMinY = Math.floor(minY - margin);
const width = Math.ceil(maxX - minX + 2 * margin);
const height = Math.ceil(maxY - minY + 2 * margin);
const ink = penOpacity < 0 ? "#ffffff" : "#171512";
const background = penOpacity < 0 ? "#000000" : "#ffffff";

function svgPath(points) {
    return points.map(([x, y], index) => {
        const canvasX = x - viewMinX;
        const canvasY = y - viewMinY;
        return `${index === 0 ? "M" : "L"}${canvasX.toFixed(3)},${canvasY.toFixed(3)}`;
    }).join(" ");
}

const body = strokes.map(points => `<path d="${svgPath(points)}"/>`).join("\n");
const svg = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}mm" height="${height}mm">`,
    `<rect x="0" y="0" width="${width}" height="${height}" fill="${background}"/>`,
    `<g fill="none" stroke="${ink}" stroke-width="0.22" stroke-linecap="round" stroke-linejoin="round">`,
    body,
    "</g>",
    "</svg>",
    "",
].join("\n");

fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, svg, "utf8");
console.log(JSON.stringify({
    strokes: strokes.length,
    points: points.length,
    bounds: [minX, minY, maxX, maxY],
    output,
}, null, 2));
