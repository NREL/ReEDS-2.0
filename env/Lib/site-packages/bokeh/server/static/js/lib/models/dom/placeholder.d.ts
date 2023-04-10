import { DOMNode, DOMNodeView } from "./dom_node";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Index as DataIndex } from "../../core/util/templating";
import * as p from "../../core/properties";
export declare abstract class PlaceholderView extends DOMNodeView {
    model: Placeholder;
    static tag_name: "span";
    render(): void;
    abstract update(source: ColumnarDataSource, i: DataIndex | null, vars: object): void;
}
export declare namespace Placeholder {
    type Attrs = p.AttrsOf<Props>;
    type Props = DOMNode.Props;
}
export interface Placeholder extends Placeholder.Attrs {
}
export declare abstract class Placeholder extends DOMNode {
    properties: Placeholder.Props;
    __view_type__: PlaceholderView;
    constructor(attrs?: Partial<Placeholder.Attrs>);
}
//# sourceMappingURL=placeholder.d.ts.map