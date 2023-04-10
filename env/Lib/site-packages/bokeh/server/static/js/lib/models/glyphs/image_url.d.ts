import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { Arrayable, Rect, ScreenArray, Indices } from "../../core/types";
import { Anchor } from "../../core/enums";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import { XY } from "../../core/util/bbox";
export type CanvasImage = HTMLImageElement;
export type ImageURLData = XYGlyphData & {
    readonly url: p.Uniform<string>;
    readonly angle: p.Uniform<number>;
    readonly w: p.Uniform<number>;
    readonly h: p.Uniform<number>;
    readonly global_alpha: p.Uniform<number>;
    _bounds_rect: Rect;
    sw: ScreenArray;
    sh: ScreenArray;
    readonly max_w: number;
    readonly max_h: number;
    image: (CanvasImage | undefined)[];
    rendered: Indices;
    anchor: XY<number>;
};
export interface ImageURLView extends ImageURLData {
}
export declare class ImageURLView extends XYGlyphView {
    model: ImageURL;
    visuals: ImageURL.Visuals;
    protected _images_rendered: boolean;
    connect_signals(): void;
    protected _index_data(index: SpatialIndex): void;
    private _set_data_iteration;
    protected _set_data(): void;
    has_finished(): boolean;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], data?: ImageURLData): void;
    protected _render_image(ctx: Context2d, i: number, image: CanvasImage, sx: Arrayable<number>, sy: Arrayable<number>, sw: Arrayable<number>, sh: Arrayable<number>, angle: p.Uniform<number>, alpha: p.Uniform<number>): void;
    bounds(): Rect;
}
export declare namespace ImageURL {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & {
        url: p.StringSpec;
        anchor: p.Property<Anchor>;
        global_alpha: p.NumberSpec;
        angle: p.AngleSpec;
        w: p.NullDistanceSpec;
        h: p.NullDistanceSpec;
        dilate: p.Property<boolean>;
        retry_attempts: p.Property<number>;
        retry_timeout: p.Property<number>;
    };
    type Visuals = XYGlyph.Visuals;
}
export interface ImageURL extends ImageURL.Attrs {
}
export declare class ImageURL extends XYGlyph {
    properties: ImageURL.Props;
    __view_type__: ImageURLView;
    constructor(attrs?: Partial<ImageURL.Attrs>);
}
//# sourceMappingURL=image_url.d.ts.map