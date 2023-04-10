import { PanEvent, TapEvent, KeyEvent, UIEvent, MoveEvent } from "../../../core/ui_events";
import { Dimensions } from "../../../core/enums";
import * as p from "../../../core/properties";
import { Rect } from "../../glyphs/rect";
import { GlyphRenderer } from "../../renderers/glyph_renderer";
import { ColumnDataSource } from "../../sources/column_data_source";
import { EditTool, EditToolView } from "./edit_tool";
export interface HasRectCDS {
    glyph: Rect;
    data_source: ColumnDataSource;
}
export declare class BoxEditToolView extends EditToolView {
    model: BoxEditTool;
    _draw_basepoint: [number, number] | null;
    _tap(ev: TapEvent): void;
    _keyup(ev: KeyEvent): void;
    _set_extent([sx0, sx1]: [number, number], [sy0, sy1]: [number, number], append: boolean, emit?: boolean): void;
    _update_box(ev: UIEvent, append?: boolean, emit?: boolean): void;
    _doubletap(ev: TapEvent): void;
    _move(ev: MoveEvent): void;
    _pan_start(ev: PanEvent): void;
    _pan(ev: PanEvent, append?: boolean, emit?: boolean): void;
    _pan_end(ev: PanEvent): void;
}
export declare namespace BoxEditTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = EditTool.Props & {
        dimensions: p.Property<Dimensions>;
        num_objects: p.Property<number>;
        renderers: p.Property<(GlyphRenderer & HasRectCDS)[]>;
    };
}
export interface BoxEditTool extends BoxEditTool.Attrs {
}
export declare class BoxEditTool extends EditTool {
    properties: BoxEditTool.Props;
    __view_type__: BoxEditToolView;
    renderers: (GlyphRenderer & HasRectCDS)[];
    constructor(attrs?: Partial<BoxEditTool.Attrs>);
    tool_name: string;
    tool_icon: string;
    event_type: ("tap" | "pan" | "move")[];
    default_order: number;
}
//# sourceMappingURL=box_edit_tool.d.ts.map