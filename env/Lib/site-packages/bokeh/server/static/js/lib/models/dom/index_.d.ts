import { Placeholder, PlaceholderView } from "./placeholder";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Index as DataIndex } from "../../core/util/templating";
import * as p from "../../core/properties";
export declare class IndexView extends PlaceholderView {
    model: Index;
    update(_source: ColumnarDataSource, i: DataIndex | null, _vars: object): void;
}
export declare namespace Index {
    type Attrs = p.AttrsOf<Props>;
    type Props = Placeholder.Props;
}
export interface Index extends Index.Attrs {
}
export declare class Index extends Placeholder {
    properties: Index.Props;
    __view_type__: IndexView;
    constructor(attrs?: Partial<Index.Attrs>);
}
//# sourceMappingURL=index_.d.ts.map