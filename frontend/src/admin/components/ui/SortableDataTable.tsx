import React, { useState } from 'react';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from './table';
import { ChevronDown, ChevronUp, ChevronsUpDown } from 'lucide-react';
import { Button } from './button';

interface SortableColumn<T> {
  key: keyof T | string;
  title: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
}

interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

interface DataTableProps<T> {
  columns: SortableColumn<T>[];
  data: T[];
  className?: string;
}

export function SortableDataTable<T extends { id: number | string }>({
  columns,
  data,
  className,
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<SortConfig>({ 
    key: 'id', 
    direction: 'asc' 
  });

  const handleSort = (key: string) => {
    setSortConfig(current => ({
      key,
      direction:
        current.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getSortedData = () => {
    const sorted = [...data].sort((a: any, b: any) => {
      if (sortConfig.key.includes('.')) {
        const keys = sortConfig.key.split('.');
        let aVal = a;
        let bVal = b;
        for (const key of keys) {
          aVal = aVal[key];
          bVal = bVal[key];
        }
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      } else {
        if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
        if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      }
    });
    return sorted;
  };

  const getSortIcon = (key: string) => {
    if (sortConfig.key !== key) return <ChevronsUpDown className="w-4 h-4" />;
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  return (
    <Table className={className}>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={column.key.toString()}>
              {column.sortable !== false ? (
                <Button
                  variant="ghost"
                  onClick={() => handleSort(column.key.toString())}
                  className="flex items-center gap-1 hover:bg-transparent"
                >
                  {column.title}
                  {getSortIcon(column.key.toString())}
                </Button>
              ) : (
                column.title
              )}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {getSortedData().map((item) => (
          <TableRow key={item.id}>
            {columns.map((column) => (
              <TableCell key={`${item.id}-${String(column.key)}`}>
                {column.render
                  ? column.render(item)
                  : (item as any)[column.key]}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}