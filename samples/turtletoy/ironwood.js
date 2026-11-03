// Ironwood
// A woodcut-inspired lumberjack, felling axe, and chopping block.
// Paste this entire file into https://turtletoy.net/turtle/new

Canvas.setpenopacity(1);

const beardDensity = 1.05;   // min=0.5, max=1.8, step=0.05
const shirtDensity = 4.2;    // min=2.5, max=7, step=0.1
const woodDensity = 3.4;     // min=2, max=6, step=0.1
const backgroundTrees = 4;   // min=2, max=8, step=1
const seed = 741852;         // min=1, max=999999, step=1

const turtle = new Turtle();
const strokes = [];
const TAU = Math.PI * 2;

function randomFactory(state) {
    return function () {
        state |= 0;
        state = (state + 0x6D2B79F5) | 0;
        let t = Math.imul(state ^ (state >>> 15), 1 | state);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

const random = randomFactory(seed);

function add(points, closed = false) {
    if (points.length < 2) return;
    const copy = points.map(point => [point[0], point[1]]);
    if (closed && (copy[0][0] !== copy[copy.length - 1][0] ||
        copy[0][1] !== copy[copy.length - 1][1])) {
        copy.push(copy[0]);
    }
    strokes.push(copy);
}

function curve(points, samples = 14, closed = false) {
    if (points.length < 2) return;
    const controls = closed
        ? [points[points.length - 1], ...points, points[0], points[1]]
        : [points[0], ...points, points[points.length - 1]];
    const result = [];
    for (let span = 1; span < controls.length - 2; span++) {
        const [a, b, c, d] = controls.slice(span - 1, span + 3);
        for (let sample = 0; sample < samples; sample++) {
            const t = sample / samples;
            const t2 = t * t;
            const t3 = t2 * t;
            result.push([
                0.5 * (
                    2 * b[0] + (-a[0] + c[0]) * t +
                    (2 * a[0] - 5 * b[0] + 4 * c[0] - d[0]) * t2 +
                    (-a[0] + 3 * b[0] - 3 * c[0] + d[0]) * t3
                ),
                0.5 * (
                    2 * b[1] + (-a[1] + c[1]) * t +
                    (2 * a[1] - 5 * b[1] + 4 * c[1] - d[1]) * t2 +
                    (-a[1] + 3 * b[1] - 3 * c[1] + d[1]) * t3
                ),
            ]);
        }
    }
    if (!closed) result.push(points[points.length - 1]);
    add(result, closed);
}

function ellipse(cx, cy, rx, ry, samples = 72, rotation = 0) {
    const angleOffset = rotation * Math.PI / 180;
    const cosine = Math.cos(angleOffset);
    const sine = Math.sin(angleOffset);
    const points = [];
    for (let i = 0; i <= samples; i++) {
        const angle = TAU * i / samples;
        const x = rx * Math.cos(angle);
        const y = ry * Math.sin(angle);
        points.push([
            cx + x * cosine - y * sine,
            cy + x * sine + y * cosine,
        ]);
    }
    add(points);
}

function hatchPolygon(polygon, spacing, angleDegrees, phase = 0) {
    const angle = angleDegrees * Math.PI / 180;
    const cosine = Math.cos(-angle);
    const sine = Math.sin(-angle);
    const rotated = polygon.map(([x, y]) => [
        x * cosine - y * sine,
        x * sine + y * cosine,
    ]);
    const minY = Math.min(...rotated.map(point => point[1]));
    const maxY = Math.max(...rotated.map(point => point[1]));
    for (let y = minY + phase; y <= maxY; y += spacing) {
        const crossings = [];
        for (let index = 0; index < rotated.length; index++) {
            const a = rotated[index];
            const b = rotated[(index + 1) % rotated.length];
            if ((a[1] > y) === (b[1] > y)) continue;
            const t = (y - a[1]) / (b[1] - a[1]);
            crossings.push(a[0] + t * (b[0] - a[0]));
        }
        crossings.sort((a, b) => a - b);
        for (let index = 0; index + 1 < crossings.length; index += 2) {
            const x0 = crossings[index];
            const x1 = crossings[index + 1];
            if (x1 - x0 < 0.35) continue;
            const backCos = Math.cos(angle);
            const backSin = Math.sin(angle);
            add([
                [x0 * backCos - y * backSin, x0 * backSin + y * backCos],
                [x1 * backCos - y * backSin, x1 * backSin + y * backCos],
            ]);
        }
    }
}

function pineTree(x, baseY, height, width, branches) {
    add([[x, baseY - height], [x, baseY]]);
    for (let tier = 0; tier < branches; tier++) {
        const t = (tier + 1) / branches;
        const y = baseY - height * (0.18 + 0.70 * t);
        const half = width * (1 - 0.62 * t);
        add([
            [x - half, y + 10],
            [x, y - 8 - 2 * Math.sin(tier * 1.9)],
            [x + half, y + 10],
        ]);
        add([
            [x - half * 0.68, y + 16],
            [x, y + 3],
            [x + half * 0.68, y + 16],
        ]);
    }
}

const shirt = [
    [-55, -31], [-43, -37], [-24, -34], [-12, -27],
    [-7, -17], [-11, 8], [-18, 30], [-49, 30],
    [-61, 10], [-62, -13],
];
const face = [
    [-46, -67], [-31, -69], [-22, -60], [-20, -50],
    [-24, -40], [-32, -35], [-41, -38], [-48, -48],
];
const cap = [
    [-50, -63], [-45, -74], [-31, -77], [-19, -68],
    [-18, -61], [-49, -59],
];
const beard = [
    [-47, -53], [-44, -42], [-39, -35], [-33, -32],
    [-25, -40], [-21, -49], [-27, -47], [-32, -42],
    [-37, -46], [-42, -43],
];
const leftLeg = [[-52, 25], [-31, 25], [-36, 66], [-51, 65]];
const rightLeg = [[-28, 25], [-10, 25], [-11, 66], [-26, 65]];
const leftBoot = [[-53, 64], [-35, 65], [-31, 75], [-54, 76], [-57, 71]];
const rightBoot = [[-28, 65], [-11, 66], [-7, 75], [-28, 76], [-31, 69]];
const axeHead = [[49, 39], [60, 35], [73, 39], [79, 45], [71, 50], [59, 49], [51, 45]];
const axeHandle = [[15, -1], [20, -3], [53, 41], [49, 47], [12, 3]];
const blockFace = [[22, 50], [88, 50], [82, 76], [29, 76]];

// Background: a restrained treeline and a rising-sun crown.
for (let i = 0; i < backgroundTrees; i++) {
    const x = (i % 2
        ? -70 - 2 * Math.sin(i * 1.7)
        : 76 + 2 * Math.cos(i * 1.3)) + 2.5 * (random() - 0.5);
    const y = 47 + (i % 3) * 1.5 + random();
    pineTree(x, y, 102 - i * 4, 19 - i * 1.1, 5);
}
for (let i = 0; i < 17; i++) {
    const angle = Math.PI + Math.PI * (i + 0.5) / 17;
    const inner = 29;
    const outer = 42 + 3 * Math.sin(i * 2.1);
    add([
        [-35 + Math.cos(angle) * inner, -52 + Math.sin(angle) * inner],
        [-35 + Math.cos(angle) * outer, -52 + Math.sin(angle) * outer],
    ]);
}
add([[-95, 76], [-7, 76]]);
add([[15, 76], [96, 76]]);

// Chopping block.
ellipse(55, 50, 33, 6, 96);
curve(blockFace, 8, true);
for (let ring = 1; ring <= 4; ring++) {
    ellipse(55, 50, ring * 6.3, ring * 1.05, 72);
}
hatchPolygon(blockFace, woodDensity, 84, 1.2);
for (let i = 0; i < 15; i++) {
    const x = 27 + i * 4.1;
    const y0 = 53 + 1.5 * Math.sin(i * 1.4) + 0.5 * random();
    add([[x, y0], [x - 0.8, 73 - 1.8 * Math.cos(i)]]);
}

// Axe handle and blade.
curve(axeHandle, 10, true);
hatchPolygon(axeHandle, 1.7, 64, 0.9);
for (let i = 0; i < 4; i++) {
    add([[17 + i * 8, 2 + i * 10], [20 + i * 8, 0 + i * 10]]);
}
curve(axeHead, 8, true);
hatchPolygon(axeHead, beardDensity, 18, 0.8);
curve([[51, 45], [60, 48], [71, 48], [78, 44]], 10);
ellipse(24, 2, 5, 7, 36, -24);

// Boots, trousers, shirt, arms, and face.
curve(leftBoot, 7, true);
curve(rightBoot, 7, true);
hatchPolygon(leftBoot, 1.4, 18);
hatchPolygon(rightBoot, 1.4, 18);
curve(leftLeg, 7, true);
curve(rightLeg, 7, true);
hatchPolygon(leftLeg, 4.8, 74);
hatchPolygon(rightLeg, 4.8, 74);

curve(shirt, 7, true);
hatchPolygon(shirt, shirtDensity, 42, 0.7);
hatchPolygon(shirt, shirtDensity * 1.4, -42, 1.1);
add([[-42, -33], [-38, 28]]);
add([[-23, -34], [-18, 28]]);
ellipse(-39, -14, 1.5, 1.5, 20);
ellipse(-38, -3, 1.5, 1.5, 20);
ellipse(-37, 8, 1.5, 1.5, 20);

// Right arm reaches the axe handle.
const rightArm = [[-13, -27], [1, -24], [14, -9], [18, 1], [12, 9], [6, 4], [-2, -5], [-11, -10]];
curve(rightArm, 8, true);
hatchPolygon(rightArm, 4.6, 38);

// Left arm rests at the hip.
const leftArm = [[-57, -21], [-67, -8], [-66, 15], [-58, 24], [-52, 20], [-56, 7], [-53, -8]];
curve(leftArm, 8, true);
hatchPolygon(leftArm, 4.8, -35);

// Neck, head, knit cap, beard, and face.
add([[-40, -37], [-39, -30]]);
add([[-28, -37], [-29, -30]]);
curve(face, 10, true);
curve(cap, 8, true);
hatchPolygon(cap, 1.35, 8, 0.5);
curve(beard, 8, true);
hatchPolygon(beard, beardDensity, 56, 0.4);

add([[-43, -57], [-35, -59]]);
add([[-33, -59], [-25, -57]]);
add([[-42, -54], [-36, -54]]);
add([[-32, -54], [-26, -54]]);
add([[-36, -53], [-34, -49], [-37, -47]]);
add([[-39, -42], [-33, -41]]);

// Flannel seams and suspenders.
add([[-50, -28], [-24, 26]]);
add([[-16, -26], [-44, 26]]);
add([[-30, -30], [-26, 29]]);
add([[-54, -7], [-11, -5]]);

function walk(i) {
    if (i >= strokes.length) return false;
    const stroke = strokes[i];
    turtle.jump(stroke[0][0], stroke[0][1]);
    turtle.pendown();
    for (let index = 1; index < stroke.length; index++) {
        turtle.goto(stroke[index][0], stroke[index][1]);
    }
    turtle.penup();
    return true;
}
