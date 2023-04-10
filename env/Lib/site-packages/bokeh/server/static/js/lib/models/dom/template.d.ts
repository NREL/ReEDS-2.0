import { DOMElement, DOMElementView } from "./dom_element";
import { Action } from "./action";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Index as DataIndex } from "../../core/util/templating";
import { ViewStorage, IterViews } from "../../core/build_views";
import * as p from "../../core/properties";
export declare class TemplateView extends DOMElementView {
    model: Template;
    static tag_name: "div";
    readonly action_views: ViewStorage<Action>;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    remove(): void;
    update(source: ColumnarDataSource, i: DataIndex | null, vars?: object): void;
}
export declare namespace Template {
    type Attrs = p.AttrsOf<Props>;
    type Props = DOMElement.Props & {
        actions: p.Property<Action[]>;
    };
}
export interface Template extends Template.Attrs {
}
export declare class Template extends DOMElement {
    properties: Template.Props;
    __view_type__: TemplateView;
}
//# sourceMappingURL=template.d.ts.map