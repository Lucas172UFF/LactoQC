from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Boolean, Table, Text, UniqueConstraint
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
raw_material_receipts = Table(
    "raw_material_receipts",
    metadata,
    Column("id_", Integer, primary_key=True, autoincrement=False),
    Column("status", Enum(RawMaterialReceiptStatus), nullable=False),
)
 
production_batches = Table(
    "production_batches",
    metadata,
    Column("id_", Integer, primary_key=True, autoincrement=False),
    Column("batch_number", String(64), unique=True, nullable=False),
    Column("production_date", DateTime, nullable=False),
    Column("milk_type", Enum(MilkType), nullable=False),
    Column("raw_material_receipt_id", Integer, ForeignKey("raw_material_receipts.id_"), nullable=False),
    Column("expected_weight", Float, nullable=False),
    Column("wettability_result", Enum(TestResult), nullable=False, default=TestResult.PENDING),
    Column("status", Enum(BatchStatus), nullable=False, default=BatchStatus.OPEN),
)
 
weight_samples = Table(
    "weight_samples",
    metadata,
    Column("id_", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", Integer, ForeignKey("production_batches.id_"), nullable=False),
    Column("date_time", DateTime, nullable=False),
    Column("weight_kg", Float, nullable=False),
)
 
lecithinizations = Table(
    "lecithinizations",
    metadata,
    Column("id_", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", Integer, ForeignKey("production_batches.id_"), unique=True, nullable=False),
    Column("performed", Boolean, nullable=False),
    Column("date_time", DateTime, nullable=True),
    Column("responsible", String(128), nullable=True),
)
 
batch_non_conformities = Table(
    "batch_non_conformities",
    metadata,
    Column("id_", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", Integer, ForeignKey("production_batches.id_"), nullable=False),
    Column("description", String(512), nullable=False),
)
 
 
def start_mappers_production_batch():
    receipt_mapper = mapper_registry.map_imperatively(
        RawMaterialReceipt,
        raw_material_receipts,
    )
 
    mapper_registry.map_imperatively(WeightSample, weight_samples)
    mapper_registry.map_imperatively(Lecithinization, lecithinizations)
    mapper_registry.map_imperatively(BatchNonConformity, batch_non_conformities)
 
    mapper_registry.map_imperatively(
        ProductionBatch,
        production_batches,
        properties={
            "raw_material_receipt": relationship(receipt_mapper),
            "weight_samples": relationship(
                WeightSample,
                collection_class=list,
                cascade="all, delete-orphan",
            ),
            "lecithinization": relationship(
                Lecithinization,
                uselist=False,
                cascade="all, delete-orphan",
            ),
            "non_conformities": relationship(
                BatchNonConformity,
                collection_class=list,
                cascade="all, delete-orphan",
            ),
        },
    )