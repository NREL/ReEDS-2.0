import { Glyph, GlyphView, GlyphData } from "./glyph";
import { PointGeometry, RectGeometry, SpanGeometry } from "../../core/geometry";
import * as p from "../../core/properties";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Rect, FloatArray, ScreenArray } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import * as visuals from "../../core/visuals";
import { HexTileOrientation } from "../../core/enums";
import { Selection } from "../selections/selection";
export type Vertices = [number, number, number, number, number, number];
export type HexTileData = GlyphData & p.UniformsOf<HexTile.Mixins> & {
    readonly q: p.Uniform<number>;
    readonly r: p.Uniform<number>;
    _x: FloatArray;
    _y: FloatArray;
    readonly scale: p.Uniform<number>;
    sx: ScreenArray;
    sy: ScreenArray;
    svx: Vertices;
    svy: Vertices;
};
export interface HexTileView extends HexTileData {
}
export declare class HexTileView extends GlyphView {
    model: HexTile;
    visuals: HexTile.Visuals;
    lazy_initialize(): Promise<void>;
    scenterxy(i: number): [number, number];
    protected _set_data(): void;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    map_data(): void;
    protected _get_unscaled_vertices(): [[number, number, number, number, number, number], [number, number, number, number, number, number]];
    protected _render(ctx: Context2d, indices: number[], data?: HexTileData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    protected _hit_rect(geometry: RectGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace HexTile {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        r: p.NumberSpec;
        q: p.NumberSpec;
        scale: p.NumberSpec;
        size: p.Property<number>;
        aspect_scale: p.Property<number>;
        orientation: p.Property<HexTileOrientation>;
    } & Mixins;
    type Mixins = LineVector & FillVector & HatchVector;
    type Visuals = Glyph.Visuals & {
        line: visuals.LineVector;
        fill: visuals.FillVector;
        hatch: visuals.HatchVector;
    };
}
export interface HexTile extends HexTile.Attrs {
}
export declare class HexTile extends Glyph {
    properties: HexTile.Props;
    __view_type__: HexTileView;
    constructor(attrs?: Partial<HexTile.Attrs>);
}
//# sourceMappingURL=hex_tile.d.ts.map