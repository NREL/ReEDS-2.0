import { Line, LineScalar, LineVector } from "./line";
import { Fill, FillScalar, FillVector } from "./fill";
import { Text, TextScalar, TextVector } from "./text";
import { Hatch, HatchScalar, HatchVector } from "./hatch";
import { Image, ImageScalar, ImageVector } from "./image";
export { Line, LineScalar, LineVector };
export { Fill, FillScalar, FillVector };
export { Text, TextScalar, TextVector };
export { Hatch, HatchScalar, HatchVector };
export { Image, ImageScalar, ImageVector };
import { View } from "../view";
import { VisualProperties, VisualUniforms, Renderable } from "./visual";
export { VisualProperties, VisualUniforms, type Renderable };
export declare class Visuals {
    [Symbol.iterator](): Generator<VisualProperties | VisualUniforms, void, undefined>;
    protected _visuals: (VisualProperties | VisualUniforms)[];
    constructor(view: View & Renderable);
}
//# sourceMappingURL=index.d.ts.map