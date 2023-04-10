import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry } from "../../core/geometry";
import * as visuals from "../../core/visuals";
import { Rect } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import * as mixins from "../../core/property_mixins";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export type PatchData = XYGlyphData & p.UniformsOf<Patch.Mixins>;
export interface PatchView extends PatchData {
}
export declare class PatchView extends XYGlyphView {
    model: Patch;
    visuals: Patch.Visuals;
    protected _render(ctx: Context2d, indices: number[], data?: PatchData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, _index: number): void;
    protected _hit_point(geometry: PointGeometry): Selection;
}
export declare namespace Patch {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & Mixins;
    type Mixins = mixins.LineScalar & mixins.FillScalar & mixins.HatchScalar;
    type Visuals = XYGlyph.Visuals & {
        line: visuals.LineScalar;
        fill: visuals.FillScalar;
        hatch: visuals.HatchScalar;
    };
}
export interface Patch extends Patch.Attrs {
}
export declare class Patch extends XYGlyph {
    properties: Patch.Props;
    __view_type__: PatchView;
    constructor(attrs?: Partial<Patch.Attrs>);
}
//# sourceMappingURL=patch.d.ts.map