import React from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from '@/components/ui/separator';

const ROLES = [
  "Engineer",
  "Designer", 
  "Product Manager",
  "Marketing",
  "Sales",
  "Operations",
  "Finance",
];

export const SearchOptions = ({ searchType, onSearchTypeChange, roleFilter, onRoleFilterChange }) => {
  return (
    <div className="space-y-4">
      {/* Temporarily hiding company search
      <div className="space-y-3">
        <Label>Search Type</Label>
        <RadioGroup 
          value={searchType}
          onValueChange={onSearchTypeChange}
          className="flex gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="profile" id="profile" />
            <Label htmlFor="profile" className="cursor-pointer">Profiles</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="company" id="company" />
            <Label htmlFor="company" className="cursor-pointer">Companies</Label>
          </div>
        </RadioGroup>
      </div>
      */}

      <div className="space-y-3">
        <Label>Role Filter</Label>
        <Select 
          value={roleFilter || "all"} 
          onValueChange={(value) => onRoleFilterChange(value === "all" ? null : value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {ROLES.map((role) => (
              <SelectItem key={role} value={role}>
                {role}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};