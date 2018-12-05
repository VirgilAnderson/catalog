import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class magicCategory(Base):

    __tablename__ = 'magicCategory'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)

    @property
    def serialize(self):
        return {
        'name' : self.name
        }


class Item(Base):

    __tablename__ = 'item'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(String(8))
    category_id = Column(Integer, ForeignKey('magicCategory.id'))
    category = relationship(magicCategory)

    @property
    def serialize(self):
        return {
        'id' : self.id,
        'name' : self.name,
        'price' : self.price,
        'description' : self.description,
        }

engine = create_engine('sqlite:///magicCatalog.db')
Base.metadata.create_all(engine)
