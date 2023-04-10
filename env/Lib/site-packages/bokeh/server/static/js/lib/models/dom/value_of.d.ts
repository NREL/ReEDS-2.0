import { DOMNode, DOMNodeView } from "./dom_node";
import { HasProps } from "../../core/has_props";
import * as p from "../../core/properties";
export declare class ValueOfView extends DOMNodeView {
    model: ValueOf;
    el: HTMLElement;
    connect_signals(): void;
    render(): void;
}
export declare namespace ValueOf {
    type Attrs = p.AttrsOf<Props>;
    type Props = DOMNode.Props & {
        obj: p.Property<HasProps>;
        attr: p.Property<string>;
    };
}
export interface ValueOf extends ValueOf.Attrs {
}
export declare class ValueOf extends DOMNode {
    properties: ValueOf.Props;
    __view_type__: ValueOfView;
    constructor(attrs?: Partial<ValueOf.Attrs>);
}
//# sourceMappingURL=value_of.d.ts.map