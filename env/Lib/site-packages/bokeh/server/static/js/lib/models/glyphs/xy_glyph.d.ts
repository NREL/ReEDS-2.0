import { FloatArray, ScreenArray } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
import { Glyph, GlyphView, GlyphData } from "./glyph";
export type XYGlyphData = GlyphData & {
    _x: FloatArray;
    _y: FloatArray;
    sx: ScreenArray;
    sy: ScreenArray;
};
export interface XYGlyphView extends XYGlyphData {
}
export declare abstract class XYGlyphView extends GlyphView {
    model: XYGlyph;
    visuals: XYGlyph.Visuals;
    protected _project_data(): void;
    protected _index_data(index: SpatialIndex): void;
    scenterxy(i: number): [number, number];
}
export declare namespace XYGlyph {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        x: p.CoordinateSpec;
        y: p.CoordinateSpec;
    };
    type Visuals = Glyph.Visuals;
}
export interface XYGlyph extends XYGlyph.Attrs {
}
export declare abstract class XYGlyph extends Glyph {
    properties: XYGlyph.Props;
    __view_type__: XYGlyphView;
    constructor(attrs?: Partial<XYGlyph.Attrs>);
}
//# sourceMappingURL=xy_glyph.d.ts.map