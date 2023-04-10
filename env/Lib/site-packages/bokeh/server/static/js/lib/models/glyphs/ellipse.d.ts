import { CenterRotatable, CenterRotatableView, CenterRotatableData } from "./center_rotatable";
import { PointGeometry } from "../../core/geometry";
import { Rect } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
import * as p from "../../core/properties";
export type EllipseData = CenterRotatableData;
export interface EllipseView extends EllipseData {
}
export declare class EllipseView extends CenterRotatableView {
    model: Ellipse;
    visuals: Ellipse.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: EllipseData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, { x0, y0, x1, y1 }: Rect, index: number): void;
}
export declare namespace Ellipse {
    type Attrs = p.AttrsOf<Props>;
    type Props = CenterRotatable.Props;
    type Visuals = CenterRotatable.Visuals;
}
export interface Ellipse extends Ellipse.Attrs {
}
export declare class Ellipse extends CenterRotatable {
    properties: Ellipse.Props;
    __view_type__: EllipseView;
    constructor(attrs?: Partial<Ellipse.Attrs>);
}
//# sourceMappingURL=ellipse.d.ts.map