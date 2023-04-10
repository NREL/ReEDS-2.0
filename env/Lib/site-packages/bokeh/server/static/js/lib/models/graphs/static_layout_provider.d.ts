import { LayoutProvider } from "./layout_provider";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace StaticLayoutProvider {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutProvider.Props & {
        graph_layout: p.Property<Map<number, Arrayable<number>>>;
    };
}
export interface StaticLayoutProvider extends StaticLayoutProvider.Attrs {
}
export declare class StaticLayoutProvider extends LayoutProvider {
    properties: StaticLayoutProvider.Props;
    constructor(attrs?: Partial<StaticLayoutProvider.Attrs>);
    get_node_coordinates(node_source: ColumnarDataSource): [Arrayable<number>, Arrayable<number>];
    get_edge_coordinates(edge_source: ColumnarDataSource): [Arrayable<number>[], Arrayable<number>[]];
}
//# sourceMappingURL=static_layout_provider.d.ts.map