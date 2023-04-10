import { SpatialIndex } from "../../core/util/spatial";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { Rect, FloatArray, ScreenArray, Indices } from "../../core/types";
import { PointGeometry, RectGeometry } from "../../core/geometry";
import { Context2d } from "../../core/util/canvas";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export type MultiPolygonsData = GlyphData & p.UniformsOf<MultiPolygons.Mixins> & {
    _xs: FloatArray[][][];
    _ys: FloatArray[][][];
    sxs: ScreenArray[][][];
    sys: ScreenArray[][][];
};
export interface MultiPolygonsView extends MultiPolygonsData {
}
export declare class MultiPolygonsView extends GlyphView {
    model: MultiPolygons;
    visuals: MultiPolygons.Visuals;
    protected _hole_index: SpatialIndex;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    protected _index_hole_data(): SpatialIndex;
    protected _mask_data(): Indices;
    protected _render(ctx: Context2d, indices: number[], data?: MultiPolygonsData): void;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_point(geometry: PointGeometry): Selection;
    private _get_snap_coord;
    scenterxy(i: number, sx: number, sy: number): [number, number];
    map_data(): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace MultiPolygons {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        xs: p.CoordinateSeqSeqSeqSpec;
        ys: p.CoordinateSeqSeqSeqSpec;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface MultiPolygons extends MultiPolygons.Attrs {
}
export declare class MultiPolygons extends Glyph {
    properties: MultiPolygons.Props;
    __view_type__: MultiPolygonsView;
    constructor(attrs?: Partial<MultiPolygons.Attrs>);
}
//# sourceMappingURL=multi_polygons.d.ts.map