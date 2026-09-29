from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship, registry
from LactoQC.domain.model import (
    CollectionPoint,
    Specification,
    MeasurementType,
    MeasurementUnit,
    Measurement,
    NonConformity,
    DailyClosure
)

mapper_registry = registry()
metadata = mapper_registry.metadata

collection_points_table = Table(
    "collection_points",
    metadata,
    Column("id", Integer, primary_key=True),              
    Column("name", String(255), nullable=False),         
    Column("location", String(255), nullable=False),  
)    

specifications_table = Table(
    "specifications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),                        
    Column("collection_point_id", Integer, ForeignKey("collection_points.id"), nullable=False),  
    Column("measurement_type", Enum(MeasurementType), nullable=False), 
    Column("min_value", Float, nullable=False),                          
    Column("max_value", Float, nullable=False),                         
    Column("measurement_unit", Enum(MeasurementUnit), nullable=True),   
)

measurements_table = Table(
    "measurements",
    metadata,
    Column("id", Integer, primary_key=True),                                                  
    Column("collection_point_id", Integer, ForeignKey("collection_points.id"), nullable=False), 
    Column("measurement_date", DateTime, nullable=False),                
    Column("value", Float, nullable=False),                              
    Column("measurement_unit", Enum(MeasurementUnit), nullable=True),   
    Column("measurement_type", Enum(MeasurementType), nullable=False),  
)

non_conformities_table = Table(
    "non_conformities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),                                
    Column("collection_point_id", Integer, ForeignKey("collection_points.id"), nullable=False), 
    Column("number", Integer, nullable=False),                                                 
    Column("measurement_id", Integer, ForeignKey("measurements.id"), nullable=False),          
    Column("specification_id", Integer, ForeignKey("specifications.id"), nullable=False),      
    Column("description", Text, nullable=False),                                               
)

daily_closures_table = Table(
    "daily_closures",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("collection_point_id", Integer, ForeignKey("collection_points.id"), nullable=False),
    Column("day", Date, nullable=False),
    UniqueConstraint("collection_point_id", "day"),
)

def start_mappers():
    mapper_registry.map_imperatively(
        Specification,
        specifications_table,
        properties={"_id": specifications_table.c.id},
    )
    mapper_registry.map_imperatively(
        Measurement,
        measurements_table,
        properties={"id_": measurements_table.c.id},
    )
    mapper_registry.map_imperatively(
        NonConformity,
        non_conformities_table,
        properties={
            "_id": non_conformities_table.c.id,
            "id_": non_conformities_table.c.number,
            "measurement": relationship(Measurement),
            "specification": relationship(Specification),
        },
    )
    mapper_registry.map_imperatively(
        DailyClosure,
        daily_closures_table,
        properties={"_id": daily_closures_table.c.id}
    )
    mapper_registry.map_imperatively(
        CollectionPoint,
        collection_points_table,
        properties={
            "id_": collection_points_table.c.id,
            "specifications": relationship(Specification, order_by=specifications_table.c.id),
            "measurements": relationship(Measurement, order_by=measurements_table.c.id),
            "non_conformities": relationship(NonConformity, order_by=non_conformities_table.c.number),
            "daily_closures": relationship(DailyClosure, order_by=daily_closures_table.c.day),
        },
    )
