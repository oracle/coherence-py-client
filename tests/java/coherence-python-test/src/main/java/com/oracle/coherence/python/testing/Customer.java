/*
 * Copyright (c) 2022 Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v 1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */


package com.oracle.coherence.python.testing;

import javax.json.bind.annotation.JsonbProperty;
import java.io.Serializable;

/**
 * Class to represent a customer.
 *
 * @author Tim Middleton 2022-12-22
 */
public class Customer
        implements Serializable {

    @JsonbProperty("id")
    private int id;

    @JsonbProperty("customerName")
    private String  customerName;

    @JsonbProperty("homeAddress")
    private Address homeAddress;

    @JsonbProperty("postalAddress")
    private Address postalAddress;

    @JsonbProperty("customerType")
    private String customerType;

    @JsonbProperty("outstandingBalance")
    private double outstandingBalance;

    public static String BRONZE = "BRONZE";
    public static String SILVER = "SILVER";
    public static String GOLD = "GOLD";

    public Customer() {}

    public Customer(int id, String customerName, Address officeAddress, Address postalAddress, String customerType, double outstandingBalance) {
        this.id = id;
        this.customerName = customerName;
        this.homeAddress = officeAddress;
        this.postalAddress = postalAddress;
        this.customerType = customerType;
        this.outstandingBalance = outstandingBalance;
    }


    @Override
    public String toString() {
        return "Customer{" +
               "id=" + id +
               ", customerName='" + customerName + '\'' +
               ", officeAddress=" + homeAddress +
               ", postalAddress=" + postalAddress +
               ", customerType='" + customerType + '\'' +
               ", outstandingBalance=" + outstandingBalance +
               '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        Customer customer = (Customer) o;

        if (id != customer.id) return false;
        if (Double.compare(customer.outstandingBalance, outstandingBalance) != 0) return false;
        if (customerName != null ? !customerName.equals(customer.customerName) : customer.customerName != null) return false;
        if (homeAddress != null ? !homeAddress.equals(customer.homeAddress) : customer.homeAddress != null) return false;
        if (postalAddress != null ? !postalAddress.equals(customer.postalAddress) : customer.postalAddress != null) return false;
        return customerType != null ? customerType.equals(customer.customerType) : customer.customerType == null;
    }

    @Override
    public int hashCode() {
        int  result;
        long temp;
        result = id;
        result = 31 * result + (customerName != null ? customerName.hashCode() : 0);
        result = 31 * result + (homeAddress != null ? homeAddress.hashCode() : 0);
        result = 31 * result + (postalAddress != null ? postalAddress.hashCode() : 0);
        result = 31 * result + (customerType != null ? customerType.hashCode() : 0);
        temp = Double.doubleToLongBits(outstandingBalance);
        result = 31 * result + (int) (temp ^ (temp >>> 32));
        return result;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public Address getHomeAddress() {
        return homeAddress;
    }

    public void setHomeAddress(Address homeAddress) {
        this.homeAddress = homeAddress;
    }

    public Address getPostalAddress() {
        return postalAddress;
    }

    public void setPostalAddress(Address postalAddress) {
        this.postalAddress = postalAddress;
    }

    public String getCustomerType() {
        return customerType;
    }

    public void setCustomerType(String customerType) {
        this.customerType = customerType;
    }

    public double getOutstandingBalance() {
        return outstandingBalance;
    }

    public void setOutstandingBalance(double outstandingBalance) {
        this.outstandingBalance = outstandingBalance;
    }
}
