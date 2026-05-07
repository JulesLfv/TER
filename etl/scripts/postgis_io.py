def to_postgis_geom(gdf, name: str, engine, schema: str = "ter", if_exists: str = "append") -> None:
    gdf = gdf.rename_geometry("geom")
    gdf.to_postgis(name, engine, schema=schema, if_exists=if_exists, index=False)
