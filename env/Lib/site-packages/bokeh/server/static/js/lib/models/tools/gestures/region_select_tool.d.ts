import { SelectTool, SelectToolView } from "./select_tool";
import { BoxAnnotation } from "../../annotations/box_annotation";
import { PolyAnnotation } from "../../annotations/poly_annotation";
import { SelectionMode } from "../../../core/enums";
import { Geometry } from "../../../core/geometry";
import { KeyModifiers } from "../../../core/ui_events";
import * as p from "../../../core/properties";
export declare abstract class RegionSelectToolView extends SelectToolView {
    model: RegionSelectTool;
    get overlays(): import("../..").Renderer[];
    protected _is_continuous(ev: KeyModifiers): boolean;
    _select(geometry: Geometry, final: boolean, mode: SelectionMode): void;
    protected _clear_overlay(): void;
}
export declare namespace RegionSelectTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = SelectTool.Props & {
        continuous: p.Property<boolean>;
        persistent: p.Property<boolean>;
    };
}
export interface RegionSelectTool extends RegionSelectTool.Attrs {
}
export declare abstract class RegionSelectTool extends SelectTool {
    properties: RegionSelectTool.Props;
    __view_type__: RegionSelectToolView;
    overlay: BoxAnnotation | PolyAnnotation;
    constructor(attrs?: Partial<RegionSelectTool.Attrs>);
}
//# sourceMappingURL=region_select_tool.d.ts.map