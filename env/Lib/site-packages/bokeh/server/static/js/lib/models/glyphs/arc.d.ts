import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import { Rect, ScreenArray } from "../../core/types";
import { Direction } from "../../core/enums";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export type ArcData = XYGlyphData & p.UniformsOf<Arc.Mixins> & {
    readonly radius: p.Uniform<number>;
    sradius: ScreenArray;
    readonly max_radius: number;
    readonly start_angle: p.Uniform<number>;
    readonly end_angle: p.Uniform<number>;
};
export interface ArcView extends ArcData {
}
export declare class ArcView extends XYGlyphView {
    model: Arc;
    visuals: Arc.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: ArcData): void;
    protected _render_decorations(ctx: Context2d, i: number, sx: number, sy: number, sradius: number, start_angle: number, end_angle: number, _anticlock: boolean): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Arc {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        direction: p.Property<Direction>;
        radius: p.DistanceSpec;
        start_angle: p.AngleSpec;
        end_angle: p.AngleSpec;
    } & Mixins;
    type Mixins = LineVector;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineVector;
    };
}
export interface Arc extends Arc.Attrs {
}
export declare class Arc extends XYGlyph {
    properties: Arc.Props;
    __view_type__: ArcView;
    constructor(attrs?: Partial<Arc.Attrs>);
}
//# sourceMappingURL=arc.d.ts.map