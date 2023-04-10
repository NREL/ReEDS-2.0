import { HitTestResult } from "../../core/hittest";
import * as p from "../../core/properties";
import * as visuals from "../../core/visuals";
import * as geometry from "../../core/geometry";
import { Context2d } from "../../core/util/canvas";
import { View } from "../../core/view";
import { Model } from "../../model";
import { Anchor } from "../../core/enums";
import { ViewStorage, IterViews } from "../../core/build_views";
import { Arrayable, Rect, ScreenArray, Indices } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import { Scale } from "../scales/scale";
import { Selection } from "../selections/selection";
import { GlyphRendererView } from "../renderers/glyph_renderer";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Decoration } from "../graphics/decoration";
export type GlyphData = {};
export interface GlyphView extends GlyphData {
}
export declare abstract class GlyphView extends View {
    model: Glyph;
    visuals: Glyph.Visuals;
    readonly parent: GlyphRendererView;
    get renderer(): GlyphRendererView;
    get has_webgl(): boolean;
    private _index;
    private _data_size;
    protected _nohit_warned: Set<geometry.Geometry["type"]>;
    get index(): SpatialIndex;
    get data_size(): number;
    initialize(): void;
    readonly decorations: ViewStorage<Decoration>;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    request_render(): void;
    get canvas(): import("../canvas/canvas").CanvasView;
    render(ctx: Context2d, indices: number[], data?: GlyphData): void;
    protected abstract _render(ctx: Context2d, indices: number[], data?: GlyphData): void;
    has_finished(): boolean;
    notify_finished(): void;
    protected _bounds(bounds: Rect): Rect;
    bounds(): Rect;
    log_bounds(): Rect;
    get_anchor_point(anchor: Anchor, i: number, [sx, sy]: [number, number]): {
        x: number;
        y: number;
    } | null;
    abstract scenterxy(i: number, sx: number, sy: number): [number, number];
    sdist(scale: Scale, pts: Arrayable<number>, spans: p.Uniform<number>, pts_location?: "center" | "edge", dilate?: boolean): ScreenArray;
    draw_legend_for_index(_ctx: Context2d, _bbox: Rect, _index: number): void;
    protected _hit_point?(geometry: geometry.PointGeometry): Selection;
    protected _hit_span?(geometry: geometry.SpanGeometry): Selection;
    protected _hit_rect?(geometry: geometry.RectGeometry): Selection;
    protected _hit_poly?(geometry: geometry.PolyGeometry): Selection;
    hit_test(geometry: geometry.Geometry): HitTestResult;
    protected _hit_rect_against_index(geometry: geometry.RectGeometry): Selection;
    protected _project_data(): void;
    private _iter_visuals;
    protected base?: this;
    set_base<T extends this>(base: T): void;
    protected _configure(prop: string | p.Property<unknown>, descriptor: PropertyDescriptor): void;
    set_visuals(source: ColumnarDataSource, indices: Indices): void;
    set_data(source: ColumnarDataSource, indices: Indices, indices_to_update?: number[]): void;
    protected _set_data(_indices: number[] | null): void;
    /**
     * Any data transformations that require visuals.
     */
    after_visuals(): void;
    private get _index_size();
    protected abstract _index_data(index: SpatialIndex): void;
    index_data(): void;
    mask_data(): Indices;
    protected _mask_data?(): Indices;
    map_data(): void;
    protected _map_data(): void;
}
export declare namespace Glyph {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        decorations: p.Property<Decoration[]>;
    };
    type Visuals = visuals.Visuals;
}
export interface Glyph extends Glyph.Attrs {
}
export declare abstract class Glyph extends Model {
    properties: Glyph.Props;
    __view_type__: GlyphView;
    constructor(attrs?: Partial<Glyph.Attrs>);
}
//# sourceMappingURL=glyph.d.ts.map