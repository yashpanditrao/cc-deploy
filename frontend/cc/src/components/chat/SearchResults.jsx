import React from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { User, Building2, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

export const SearchResults = ({ results, type }) => {
  if (!results.length) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No results found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {results.map((result) => (
        <Card key={type === 'profile' ? result.profile.id : result.company.id} className="bg-card">
          <CardHeader className="p-4 pb-2">
            <div className="flex items-center gap-3">
              <Avatar className="h-10 w-10">
                {type === 'profile' ? (
                  <>
                    <AvatarImage 
                      src={result.profile.image_url} 
                      alt={result.profile.name} 
                    />
                    <AvatarFallback>
                      <User className="h-5 w-5" />
                    </AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarImage 
                      src={result.company.image_url} 
                      alt={result.company.name}
                    />
                    <AvatarFallback>
                      <Building2 className="h-5 w-5" />
                    </AvatarFallback>
                  </>
                )}
              </Avatar>
              <div className="flex-1 min-w-0">
                <CardTitle className="text-base truncate">
                  {type === 'profile' ? result.profile.name : result.company.name}
                </CardTitle>
                {type === 'profile' && (
                  <CardDescription className="truncate">{result.profile.role}</CardDescription>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {type === 'profile' ? (
              <div className="space-y-2">
                {result.profile.education && (
                  <p className="text-xs text-muted-foreground truncate">
                    {result.profile.education}
                  </p>
                )}
                {result.profile.interests?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {result.profile.interests.slice(0, 3).map((interest, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {interest}
                      </Badge>
                    ))}
                    {result.profile.interests.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{result.profile.interests.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                {result.company.industry && (
                  <p className="text-xs text-muted-foreground truncate">
                    {result.company.industry}
                  </p>
                )}
                {result.company.location && (
                  <p className="text-xs text-muted-foreground truncate">
                    {result.company.location}
                  </p>
                )}
              </div>
            )}
          </CardContent>
          {type === 'profile' && (
            <CardFooter className="p-2 pt-0">
              <Button variant="ghost" size="sm" className="ml-auto" asChild>
                <Link to={`/profile/${result.profile.id}`}>
                  View Profile
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardFooter>
          )}
        </Card>
      ))}
    </div>
  );
}; 