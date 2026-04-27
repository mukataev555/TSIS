CREATE OR REPLACE FUNCTION get_contacts_by_pattern(pattern TEXT)
RETURNS TABLE(id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT * FROM phonebook 
    WHERE contact_name ILIKE '%' || pattern || '%' 
       OR phone_number LIKE '%' || pattern || '%';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_contacts_paged(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY SELECT * FROM phonebook 
    ORDER BY contact_name 
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;