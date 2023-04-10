import { SpatialIndex } from "../../core/util/spatial";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { Rect, RaggedArray, FloatArray, ScreenArray, Indices } from "../../core/types";
import { PointGeometry, RectGeometry } from "../../core/geometry";
import { Context2d } from "../../core/util/canvas";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export type PatchesData = GlyphData & p.UniformsOf<Patches.Mixins> & {
    _xs: RaggedArray<FloatArray>;
    _ys: RaggedArray<FloatArray>;
    sxs: RaggedArray<ScreenArray>;
    sys: RaggedArray<ScreenArray>;
};
export interface PatchesView extends PatchesData {
}
export declare class PatchesView extends GlyphView {
    model: Patches;
    visuals: Patches.Visuals;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    protected _mask_data(): Indices;
    protected _render(ctx: Context2d, indices: number[], data?: PatchesData): void;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_point(geometry: PointGeometry): Selection;
    private _get_snap_coord;
    scenterxy(i: number, sx: number, sy: number): [number, number];
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Patches {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        xs: p.CoordinateSeqSpec;
        ys: p.CoordinateSeqSpec;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface Patches extends Patches.Attrs {
}
export declare class Patches extends Glyph {
    properties: Patches.Props;
    __view_type__: PatchesView;
    constructor(attrs?: Partial<Patches.Attrs>);
}
//# sourceMappingURL=patches.d.ts.map