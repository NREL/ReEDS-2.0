import { Marker, MarkerView, MarkerData } from "./marker";
import { MarkerType } from "../../core/enums";
import { Rect } from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export type ScatterData = MarkerData & {
    readonly marker: p.Uniform<MarkerType | null>;
};
export interface ScatterView extends ScatterData {
}
export declare class ScatterView extends MarkerView {
    model: Scatter;
    lazy_initialize(): Promise<void>;
    protected _render(ctx: Context2d, indices: number[], data?: ScatterData): void;
    draw_legend_for_index(ctx: Context2d, { x0, x1, y0, y1 }: Rect, index: number): void;
}
export declare namespace Scatter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Marker.Props & {
        marker: p.MarkerSpec;
    };
}
export interface Scatter extends Scatter.Attrs {
}
export declare class Scatter extends Marker {
    properties: Scatter.Props;
    __view_type__: ScatterView;
    constructor(attrs?: Partial<Scatter.Attrs>);
}
//# sourceMappingURL=scatter.d.ts.map