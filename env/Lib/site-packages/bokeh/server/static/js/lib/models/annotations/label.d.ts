import { TextAnnotation, TextAnnotationView } from "./text_annotation";
import { CoordinateUnits, AngleUnits } from "../../core/enums";
import { Size } from "../../core/layout";
import * as p from "../../core/properties";
export declare class LabelView extends TextAnnotationView {
    model: Label;
    visuals: Label.Visuals;
    update_layout(): void;
    protected _get_size(): Size;
    protected _render(): void;
}
export declare namespace Label {
    type Props = TextAnnotation.Props & {
        x: p.Property<number>;
        x_units: p.Property<CoordinateUnits>;
        y: p.Property<number>;
        y_units: p.Property<CoordinateUnits>;
        angle: p.Property<number>;
        angle_units: p.Property<AngleUnits>;
        x_offset: p.Property<number>;
        y_offset: p.Property<number>;
    };
    type Attrs = p.AttrsOf<Props>;
    type Visuals = TextAnnotation.Visuals;
}
export interface Label extends Label.Attrs {
}
export declare class Label extends TextAnnotation {
    properties: Label.Props;
    __view_type__: LabelView;
    constructor(attrs?: Partial<Label.Attrs>);
}
//# sourceMappingURL=label.d.ts.map